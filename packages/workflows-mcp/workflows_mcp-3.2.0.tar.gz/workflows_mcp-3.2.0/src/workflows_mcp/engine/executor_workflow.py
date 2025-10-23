"""ExecuteWorkflow executor for ADR-006 fractal architecture.

This executor is special - it returns a full child Execution object (not BlockOutput),
enabling true fractal nesting where child blocks are preserved in the parent execution.
"""

from __future__ import annotations

from typing import Any, ClassVar

from pydantic import Field

from .block import BlockInput
from .exceptions import ExecutionPaused
from .execution import Execution
from .executor_base import BlockExecutor, ExecutorCapabilities, ExecutorSecurityLevel


class ExecuteWorkflowInput(BlockInput):
    """
    Input model for ExecuteWorkflow executor.

    Supports variable references from parent context:
    - ${inputs.field}: Parent workflow inputs
    - ${blocks.block_id.outputs.field}: Parent block outputs
    - ${metadata.field}: Parent workflow metadata

    Variable resolution happens in parent context before passing to child,
    so the child receives fully resolved values.
    """

    workflow: str = Field(description="Workflow name to execute")
    inputs: dict[str, Any] = Field(
        default_factory=dict,
        description="Inputs to pass to child workflow (variables resolved in parent context)",
    )
    timeout_ms: int | None = Field(
        default=None,
        description="Optional timeout for child execution in milliseconds",
    )


class ExecuteWorkflowExecutor(BlockExecutor):
    """
    Workflow composition executor (ADR-006 fully embedded fractal pattern).

    This executor is SPECIAL - it returns the full child Execution object,
    not a BlockOutput. The orchestrator recognizes this and stores the child
    Execution directly in parent.blocks, enabling true fractal nesting.

    Architecture (ADR-006):
    - Returns full child Execution (includes child's blocks!)
    - Orchestrator stores child Execution in parent.blocks[block_id]
    - Enables deep access: ${blocks.run_tests.blocks.pytest.outputs.exit_code}
    - Circular dependency detection via _internal.workflow_stack
    - Raises ExecutionPaused if child pauses (automatic bubbling)

    Fractal Pattern:
        parent_execution.blocks = {
            "run_tests": Execution(  # ← Full child execution embedded!
                outputs={"test_passed": True},
                blocks={  # ← Child's internal blocks preserved!
                    "pytest": Execution(...),
                    "coverage": Execution(...),
                }
            )
        }

    Variable Access:
        ${blocks.run_tests.outputs.test_passed}  # Child's workflow output
        ${blocks.run_tests.blocks.pytest.outputs.exit_code}  # Drill down!

    Pause Propagation:
        If child workflow pauses (Prompt block), ExecutionPaused exception
        automatically bubbles through call stack to top-level orchestrator.
        No special handling needed - it just works!

    Error Propagation:
        Any exception from child workflow (including ExecutionPaused) propagates
        to parent. Orchestrator creates appropriate Metadata.
    """

    type_name: ClassVar[str] = "ExecuteWorkflow"
    input_type: ClassVar[type[BlockInput]] = ExecuteWorkflowInput
    output_type: ClassVar[type] = type(None)  # Special: returns Execution, not BlockOutput

    security_level: ClassVar[ExecutorSecurityLevel] = ExecutorSecurityLevel.TRUSTED
    capabilities: ClassVar[ExecutorCapabilities] = ExecutorCapabilities(
        can_modify_state=True  # Can execute other workflows
    )

    async def execute(  # type: ignore[override]
        self, inputs: ExecuteWorkflowInput, context: Execution
    ) -> Execution:
        """
        Execute child workflow with full embedding.

        Args:
            inputs: Validated ExecuteWorkflowInput
            context: Parent execution context (fractal structure)

        Returns:
            Full child Execution (stored directly in parent.blocks[block_id])

        Raises:
            ValueError: Circular dependency or workflow not found
            ExecutionPaused: Child workflow paused (bubbles automatically)
            Exception: Any other child execution failure
        """
        # 1. Get executor from _internal (orchestration state)
        executor = context._internal.get("executor")
        if executor is None:
            raise RuntimeError(
                "Executor not found in context._internal - "
                "workflow composition not supported in this context"
            )

        # 2. Circular dependency detection via workflow_stack
        workflow_stack: list[str] = context._internal.get("workflow_stack", [])
        workflow_name = inputs.workflow

        if workflow_name in workflow_stack:
            cycle_path = " → ".join(workflow_stack + [workflow_name])
            raise ValueError(f"Circular dependency detected: {cycle_path}")

        # 3. Check if workflow exists in registry
        if not hasattr(executor, "workflows") or workflow_name not in executor.workflows:
            available = list(executor.workflows.keys()) if hasattr(executor, "workflows") else []
            raise ValueError(
                f"Workflow '{workflow_name}' not found in registry. "
                f"Available: {', '.join(available)}"
            )

        # 4. Execute child workflow
        # Call the private _execute_workflow_internal() method directly
        # (it will create the Execution context internally)
        #
        # This returns a full Execution object with:
        # - child_execution.inputs: What we passed in
        # - child_execution.outputs: Child's workflow-level outputs
        # - child_execution.blocks: Child's internal block executions (PRESERVED!)
        # - child_execution.metadata: Child's execution metadata
        #
        # ExecutionPaused exception must be caught and wrapped with parent metadata
        try:
            child_execution = await executor._execute_workflow_internal(
                workflow_name=workflow_name,
                runtime_inputs=inputs.inputs,
                parent_workflow_stack=workflow_stack,
            )
        except ExecutionPaused as child_pause:
            # Child workflow paused - wrap with parent-level metadata (fractal pattern)
            # Extract child's checkpoint_id from exception
            child_checkpoint_id = child_pause.checkpoint_data.get("checkpoint_id", "")

            # Re-raise with parent metadata wrapping child info
            raise ExecutionPaused(
                prompt=child_pause.prompt,  # Keep child's prompt
                checkpoint_data={
                    "child_checkpoint_id": child_checkpoint_id,
                    "child_workflow": workflow_name,
                    "child_pause_metadata": child_pause.checkpoint_data,  # Preserve child's data
                },
            )

        # 5. Return full child execution (orchestrator stores in parent.blocks)
        # This enables true fractal nesting!
        return child_execution

    async def resume(  # type: ignore[override]
        self,
        inputs: BlockInput,
        context: Execution,
        response: str,
        pause_metadata: dict[str, Any],
    ) -> Execution:
        """
        Resume child workflow execution after pause.

        When a parent workflow resumes and this block was paused (nested workflow),
        we extract the child's checkpoint_id and delegate resume to the child.

        Args:
            inputs: Original ExecuteWorkflowInput
            context: Parent execution context
            response: LLM's response to pause prompt
            pause_metadata: Pause metadata containing child_checkpoint_id

        Returns:
            Full child Execution (resumed state)

        Raises:
            ValueError: Missing checkpoint ID or workflow not found
            ExecutionPaused: Child paused again (bubbles automatically)
            Exception: Any other child execution failure
        """
        # Type assertion
        assert isinstance(inputs, ExecuteWorkflowInput)

        # 1. Extract child checkpoint ID from pause metadata
        child_checkpoint_id = pause_metadata.get("child_checkpoint_id")
        if not child_checkpoint_id:
            raise ValueError(
                "Missing child_checkpoint_id in pause_metadata - "
                "cannot resume nested workflow"
            )

        # 2. Get executor from context
        executor = context._internal.get("executor")
        if executor is None:
            raise RuntimeError(
                "Executor not found in context._internal - "
                "workflow composition not supported in this context"
            )

        # 3. Resume child workflow
        # Child's checkpoint contains full child context
        # LLM response is passed to the paused block within child
        child_execution = await executor._resume_workflow_internal(
            checkpoint_id=child_checkpoint_id,
            response=response,
        )

        # 4. Return full child execution (orchestrator stores in parent.blocks)
        # If child pauses again, ExecutionPaused bubbles automatically
        return child_execution
