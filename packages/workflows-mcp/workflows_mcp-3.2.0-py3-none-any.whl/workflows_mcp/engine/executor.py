"""
Clean ADR-006 implementation of workflow executor.

This module implements the unified execution model:
- Execution model (fractal) as context
- BlockOrchestrator for exception handling
- ExecutionPaused exception for pause propagation
- Fully embedded child executions for ExecuteWorkflow
- Clean separation of data (outputs) and state (metadata)
"""

import asyncio
import logging
import time
import uuid
from datetime import UTC, datetime
from typing import Any, Literal

from .checkpoint import CheckpointConfig, CheckpointState
from .checkpoint_store import CheckpointStore, InMemoryCheckpointStore
from .context_vars import block_custom_outputs
from .dag import DAGResolver
from .exceptions import ExecutionPaused
from .execution import Execution
from .executor_base import ExecutorRegistry
from .metadata import Metadata
from .orchestrator import BlockOrchestrator
from .response import WorkflowResponse
from .schema import BlockDefinition, DependencySpec, WorkflowSchema
from .variables import ConditionEvaluator, InvalidConditionError, VariableResolver

logger = logging.getLogger(__name__)


class WorkflowExecutor:
    """
    ADR-006 compliant workflow executor.

    Key differences from old executor:
    - Uses Execution model instead of dict context
    - Uses BlockOrchestrator for all block execution
    - Exceptions bubble naturally (no Result wrapper at block level)
    - ExecuteWorkflow stores full child Execution (fractal)
    - Simpler, cleaner implementation (~400 lines vs 1454)
    """

    def __init__(
        self,
        registry: ExecutorRegistry,
        checkpoint_store: CheckpointStore | None = None,
        checkpoint_config: CheckpointConfig | None = None,
    ) -> None:
        """Initialize the workflow executor.

        Args:
            registry: ExecutorRegistry with registered block executors
            checkpoint_store: Optional checkpoint store for pause/resume
            checkpoint_config: Optional checkpoint configuration
        """
        self.registry = registry
        self.workflows: dict[str, WorkflowSchema] = {}
        self.checkpoint_store = checkpoint_store or InMemoryCheckpointStore()
        self.checkpoint_config = checkpoint_config or CheckpointConfig()
        self.orchestrator = BlockOrchestrator()

    def load_workflow(self, workflow_schema: WorkflowSchema) -> None:
        """Load a workflow schema.

        Args:
            workflow_schema: WorkflowSchema instance to load
        """
        self.workflows[workflow_schema.name] = workflow_schema

    async def execute_workflow(
        self,
        workflow_name: str,
        runtime_inputs: dict[str, Any] | None = None,
        response_format: Literal["minimal", "detailed"] = "minimal",
    ) -> WorkflowResponse:
        """
        Execute a workflow by name.

        Args:
            workflow_name: Name of workflow to execute
            runtime_inputs: Runtime input overrides
            response_format: Output verbosity ("minimal" or "detailed")

        Returns:
            WorkflowResponse with execution results
        """
        try:
            # Execute workflow (returns Execution model)
            execution = await self._execute_workflow_internal(workflow_name, runtime_inputs)

            # Convert to WorkflowResponse
            return self._execution_to_response(execution, response_format)

        except ExecutionPaused as e:
            # Workflow paused - checkpoint already saved in _execute_workflow_internal
            # Extract checkpoint_id from exception checkpoint_data
            checkpoint_id = e.checkpoint_data.get("checkpoint_id", "")

            if not checkpoint_id:
                # Fallback: generate checkpoint_id if not present (shouldn't happen)
                logger.warning("ExecutionPaused exception missing checkpoint_id")
                timestamp = int(time.time() * 1000)
                checkpoint_id = f"pause_{workflow_name}_{timestamp}_{uuid.uuid4().hex[:8]}"

            return WorkflowResponse(
                status="paused",
                checkpoint_id=checkpoint_id,
                prompt=e.prompt,
                message=(
                    f'Use resume_workflow(checkpoint_id: "{checkpoint_id}", '
                    f'response: "<response>") to continue'
                ),
                response_format=response_format,
            )

        except Exception as e:
            logger.exception(f"Workflow execution failed: {e}")
            return WorkflowResponse(
                status="failure",
                error=str(e),
                response_format=response_format,
            )

    async def _execute_workflow_internal(
        self,
        workflow_name: str,
        runtime_inputs: dict[str, Any] | None = None,
        parent_workflow_stack: list[str] | None = None,
    ) -> Execution:
        """Execute workflow from start (fresh context, wave 0).

        Args:
            workflow_name: Name of workflow to execute
            runtime_inputs: Runtime input overrides
            parent_workflow_stack: Parent workflow stack for circular detection

        Returns:
            Execution with complete workflow state

        Raises:
            ExecutionPaused: If workflow pauses (bubbles up with checkpoint_id)
            ValueError: If workflow not found
            Exception: On execution errors
        """
        start_time = time.time()

        # 1. Get workflow schema
        if workflow_name not in self.workflows:
            raise ValueError(f"Workflow not found: {workflow_name}")
        workflow_schema = self.workflows[workflow_name]

        # 2. Create fresh execution context
        context = self._create_initial_execution_context(
            workflow_name, workflow_schema, runtime_inputs, parent_workflow_stack
        )

        # 3. Compute execution waves
        execution_waves = self._compute_execution_waves(workflow_schema)

        # 4. Execute all waves starting from 0
        completed_blocks: list[str] = []
        await self._execute_waves_from(
            start_wave_index=0,
            execution_waves=execution_waves,
            workflow_name=workflow_name,
            workflow_schema=workflow_schema,
            runtime_inputs=runtime_inputs or {},
            context=context,
            completed_blocks=completed_blocks,
        )

        # 5. Finalize context
        self._finalize_execution_context(
            workflow_schema, context, completed_blocks, execution_waves, start_time
        )

        return context

    async def _execute_wave(
        self,
        wave: list[str],
        wave_idx: int,
        context: Execution,
        workflow_schema: WorkflowSchema,
        completed_blocks: list[str],
    ) -> list[str]:
        """
        Execute a single wave of blocks in parallel.

        Args:
            wave: List of block IDs to execute
            wave_idx: Wave index
            context: Execution context
            workflow_schema: Workflow schema
            completed_blocks: Already completed block IDs

        Returns:
            List of block IDs executed in this wave

        Raises:
            ExecutionPaused: If any block pauses
        """
        # Create block lookup
        blocks_by_id = {block.id: block for block in workflow_schema.blocks}

        # Prepare execution tasks
        tasks = []
        block_ids = []

        for block_id in wave:
            block_def = blocks_by_id[block_id]

            # Check if should skip due to dependencies
            if self._should_skip_block(block_id, block_def.depends_on, context):
                self._mark_block_skipped(
                    block_id=block_id,
                    block_def=block_def,
                    context=context,
                    wave_idx=wave_idx,
                    execution_order=len(completed_blocks),
                    reason="Parent dependency did not complete successfully",
                )
                continue

            # Check condition
            if block_def.condition:
                should_execute = self._evaluate_condition(block_def.condition, context)
                if not should_execute:
                    self._mark_block_skipped(
                        block_id=block_id,
                        block_def=block_def,
                        context=context,
                        wave_idx=wave_idx,
                        execution_order=len(completed_blocks),
                        reason=f"Condition '{block_def.condition}' evaluated to False",
                    )
                    continue

            # Add to execution tasks
            execution_order = len(completed_blocks)
            task = self._execute_block(block_id, block_def, context, wave_idx, execution_order)
            tasks.append(task)
            block_ids.append(block_id)

        # Execute blocks in parallel
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Process results
            for block_id, result in zip(block_ids, results):
                if isinstance(result, ExecutionPaused):
                    # Pause bubbles up immediately
                    raise result
                elif isinstance(result, Exception):
                    # Execution error - mark as failed but continue
                    self._mark_block_failed(
                        block_id=block_id,
                        block_def=blocks_by_id[block_id],
                        context=context,
                        wave_idx=wave_idx,
                        execution_order=len(completed_blocks),
                        error=str(result),
                    )

        return block_ids

    async def _execute_block(
        self,
        block_id: str,
        block_def: BlockDefinition,
        context: Execution,
        wave_idx: int,
        execution_order: int,
    ) -> None:
        """
        Execute a single block using BlockOrchestrator.

        Args:
            block_id: Block ID
            block_def: Block definition
            context: Execution context
            wave_idx: Wave index
            execution_order: Execution order

        Raises:
            ExecutionPaused: If block pauses
            Exception: On execution errors
        """
        # 1. Resolve variables in inputs
        resolved_inputs = self._resolve_block_inputs(block_def.inputs, context)

        # 2. Get executor
        executor = self.registry.get(block_def.type)

        # 3. Create input model
        input_model = executor.input_type(**resolved_inputs)

        # 3.5. Set custom outputs using contextvars (async-safe for parallel execution)
        # This prevents race conditions when blocks with/without custom outputs run in parallel
        if block_def.outputs:
            # Convert OutputSchema models to dict format expected by Shell executor
            custom_outputs_dict = {
                name: output.model_dump() for name, output in block_def.outputs.items()
            }
            # Set context variable (async-local, no race condition)
            block_custom_outputs.set(custom_outputs_dict)
        else:
            # Clear custom outputs for this task
            block_custom_outputs.set(None)

        # 4. Execute via orchestrator
        block_execution = await self.orchestrator.execute_block(
            executor=executor,
            inputs=input_model,
            context=context,
            wave=wave_idx,
            execution_order=execution_order,
        )

        # 5. Handle pause
        if block_execution.paused:
            # Raise ExecutionPaused to bubble up
            # Add paused_block_id to checkpoint_data (fractal pattern - track pause at each level)
            pause_data = block_execution.pause_checkpoint_data or {}
            pause_data["paused_block_id"] = block_id

            raise ExecutionPaused(
                prompt=block_execution.pause_prompt or "Execution paused",
                checkpoint_data=pause_data,
            )

        # 6. Store result
        if block_def.type == "ExecuteWorkflow":
            # Special case: ExecuteWorkflow returns child Execution (fully embedded)
            if block_execution.output is None:
                # ExecuteWorkflow failed - create minimal failed Execution
                context.blocks[block_id] = Execution(
                    inputs=resolved_inputs,
                    outputs={},
                    metadata=block_execution.metadata,
                    blocks={},
                )
            else:
                # Wrap child execution with block-level metadata
                # This ensures ADR-007 shortcuts work: ${blocks.commit.succeeded}
                # - metadata: Block-level (succeeded, failed, status, outcome)
                # - outputs: Child workflow outputs
                # - blocks: Child's nested blocks for deep access
                assert isinstance(block_execution.output, Execution)
                child_exec = block_execution.output
                context.blocks[block_id] = Execution(
                    inputs=resolved_inputs,
                    outputs=child_exec.outputs,  # Child workflow outputs
                    metadata=block_execution.metadata,  # Block metadata
                    blocks=child_exec.blocks,  # Preserve child's nested blocks
                )
        else:
            # Regular block: store inputs, outputs, metadata
            context.set_block_result(
                block_id=block_id,
                inputs=resolved_inputs,
                outputs=block_execution.output.model_dump() if block_execution.output else {},
                metadata=block_execution.metadata,
            )

    def _should_skip_block(
        self,
        block_id: str,
        depends_on: list[DependencySpec],
        context: Execution,
    ) -> bool:
        """Check if block should skip due to required dependencies."""
        if not depends_on:
            return False

        for dep_spec in depends_on:
            # Check if dependency requires this block to skip
            dep_metadata = context.get_block_metadata(dep_spec.block)
            if dep_metadata:
                # Use Metadata.requires_dependent_skip() which implements ADR-006 logic
                if dep_metadata.requires_dependent_skip(required=dep_spec.required):
                    return True

        return False

    def _mark_block_skipped(
        self,
        block_id: str,
        block_def: BlockDefinition,
        context: Execution,
        wave_idx: int,
        execution_order: int,
        reason: str,
    ) -> None:
        """Mark a block as skipped."""
        skip_time = datetime.now(UTC).isoformat()
        metadata = Metadata.from_skipped(
            message=reason,
            timestamp=skip_time,
            wave=wave_idx,
            execution_order=execution_order,
        )

        # Create default outputs
        default_outputs = self._create_default_outputs(block_def.type)

        context.set_block_result(
            block_id=block_id,
            inputs={},
            outputs=default_outputs,
            metadata=metadata,
        )

    def _mark_block_failed(
        self,
        block_id: str,
        block_def: BlockDefinition,
        context: Execution,
        wave_idx: int,
        execution_order: int,
        error: str,
    ) -> None:
        """Mark a block as failed due to execution error."""
        fail_time = datetime.now(UTC).isoformat()
        metadata = Metadata.from_execution_failure(
            message=error,
            execution_time_ms=0.0,
            started_at=fail_time,
            completed_at=fail_time,
            wave=wave_idx,
            execution_order=execution_order,
        )

        default_outputs = self._create_default_outputs(block_def.type)

        context.set_block_result(
            block_id=block_id,
            inputs={},
            outputs=default_outputs,
            metadata=metadata,
        )

    def _create_default_outputs(self, block_type: str) -> dict[str, Any]:
        """Create default outputs for skipped/failed blocks."""
        try:
            executor = self.registry.get(block_type)
            output_model_class = executor.output_type

            # Get model fields
            defaults: dict[str, Any] = {}
            for field_name, field_info in output_model_class.model_fields.items():
                field_type = field_info.annotation

                # Type-based defaults
                if "str" in str(field_type):
                    defaults[field_name] = ""
                elif "int" in str(field_type):
                    defaults[field_name] = 0
                elif "float" in str(field_type):
                    defaults[field_name] = 0.0
                elif "bool" in str(field_type):
                    defaults[field_name] = False
                elif "dict" in str(field_type):
                    defaults[field_name] = {}
                elif "list" in str(field_type):
                    defaults[field_name] = []
                else:
                    defaults[field_name] = None

            return defaults

        except Exception:
            return {}

    def _create_initial_execution_context(
        self,
        workflow_name: str,
        workflow_schema: WorkflowSchema,
        runtime_inputs: dict[str, Any] | None,
        parent_workflow_stack: list[str] | None = None,
    ) -> Execution:
        """Create fresh Execution context for workflow start.

        Args:
            workflow_name: Name of workflow being executed
            workflow_schema: Workflow schema definition
            runtime_inputs: Runtime input overrides
            parent_workflow_stack: Parent workflow stack for circular detection

        Returns:
            Fresh Execution context with inputs, metadata, and internal state
        """
        context = Execution(
            inputs=self._merge_workflow_inputs(workflow_schema, runtime_inputs),
            metadata={
                "workflow_name": workflow_name,
                "start_time": datetime.now(UTC).isoformat(),
            },
            blocks={},
        )
        # Set _internal after creation (it's a PrivateAttr)
        context._internal = {
            "executor": self,
            "workflow_stack": (parent_workflow_stack or []) + [workflow_name],
        }
        return context

    def _restore_execution_context(
        self,
        checkpoint: CheckpointState,
    ) -> Execution:
        """Restore Execution context from checkpoint.

        Args:
            checkpoint: CheckpointState with saved execution state

        Returns:
            Restored Execution context with internal state
        """
        context = checkpoint.context
        workflow_stack = [ws.get("name", "") for ws in checkpoint.workflow_stack]
        context._internal = {
            "executor": self,
            "workflow_stack": workflow_stack,
        }
        return context

    def _compute_execution_waves(
        self,
        workflow_schema: WorkflowSchema,
    ) -> list[list[str]]:
        """Compute execution waves from workflow schema using DAG resolution.

        Args:
            workflow_schema: Workflow schema with blocks and dependencies

        Returns:
            List of execution waves (list of block IDs per wave)

        Raises:
            ValueError: If DAG resolution fails (cycles, invalid dependencies)
        """
        dependencies = {
            block.id: [dep.block for dep in block.depends_on]
            for block in workflow_schema.blocks
        }
        block_ids = [block.id for block in workflow_schema.blocks]

        resolver = DAGResolver(block_ids, dependencies)
        waves_result = resolver.get_execution_waves()

        if not waves_result.is_success or waves_result.value is None:
            raise ValueError(f"DAG resolution failed: {waves_result.error}")

        return waves_result.value

    def _finalize_execution_context(
        self,
        workflow_schema: WorkflowSchema,
        context: Execution,
        completed_blocks: list[str],
        execution_waves: list[list[str]],
        start_time: float | None = None,
    ) -> None:
        """Finalize execution context with outputs and metadata.

        Mutates context.outputs and context.metadata in place.

        Args:
            workflow_schema: Workflow schema for output evaluation
            context: Execution context to finalize
            completed_blocks: List of completed block IDs
            execution_waves: All execution waves
            start_time: Optional start time for execution time calculation
        """
        # Evaluate workflow outputs
        workflow_outputs = self._evaluate_workflow_outputs(workflow_schema, context)
        context.outputs = workflow_outputs

        # Update metadata
        metadata_updates: dict[str, Any] = {
            "total_blocks": len(completed_blocks),
            "execution_waves": len(execution_waves),
            "completed_at": datetime.now(UTC).isoformat(),
        }

        if start_time is not None:
            metadata_updates["execution_time_seconds"] = time.time() - start_time

        if isinstance(context.metadata, dict):
            # Preserve workflow_name and other existing fields
            existing_metadata = context.metadata.copy()
            existing_metadata.update(metadata_updates)
            context.metadata = existing_metadata
        else:
            # Metadata is a Metadata model - extract workflow_name and convert to dict
            workflow_name_value = getattr(context.metadata, "workflow_name", "")
            context.metadata = {
                "workflow_name": workflow_name_value,
                **metadata_updates,
            }

    async def _execute_waves_from(
        self,
        start_wave_index: int,
        execution_waves: list[list[str]],
        workflow_name: str,
        workflow_schema: WorkflowSchema,
        runtime_inputs: dict[str, Any],
        context: Execution,
        completed_blocks: list[str],
    ) -> None:
        """Execute workflow waves starting from given index.

        Handles wave-by-wave parallel execution with checkpoint saving
        and ExecutionPaused exception handling.

        Args:
            start_wave_index: Wave index to start from (0 for fresh, N+1 for resume)
            execution_waves: All execution waves from DAG resolution
            workflow_name: Workflow name (for checkpoint saving)
            workflow_schema: Workflow schema (for checkpoint saving)
            runtime_inputs: Runtime inputs (for checkpoint saving)
            context: Execution context (mutated with block results)
            completed_blocks: List of completed block IDs (mutated during execution)

        Raises:
            ExecutionPaused: If any block pauses (with checkpoint_id in exception)

        Note:
            - Mutates context.blocks and completed_blocks list in place
            - Saves checkpoints after each wave if configured
            - On pause, saves checkpoint and re-raises ExecutionPaused with checkpoint_id
        """
        wave_idx = start_wave_index - 1  # For exception handler

        try:
            for wave_idx in range(start_wave_index, len(execution_waves)):
                wave = execution_waves[wave_idx]

                # Execute wave
                executed_blocks = await self._execute_wave(
                    wave=wave,
                    wave_idx=wave_idx,
                    context=context,
                    workflow_schema=workflow_schema,
                    completed_blocks=completed_blocks,
                )
                completed_blocks.extend(executed_blocks)

                # Checkpoint after wave (crash recovery)
                if self.checkpoint_config.enabled and self.checkpoint_config.checkpoint_every_wave:
                    await self._save_checkpoint(
                        workflow_name=workflow_name,
                        workflow_schema=workflow_schema,
                        runtime_inputs=runtime_inputs,
                        context=context,
                        completed_blocks=completed_blocks,
                        current_wave_index=wave_idx,
                        execution_waves=execution_waves,
                    )

        except ExecutionPaused as e:
            # Workflow paused during wave execution
            # Save ONE checkpoint with pause metadata (no double-save)
            checkpoint_id = await self._save_checkpoint(
                workflow_name=workflow_name,
                workflow_schema=workflow_schema,
                runtime_inputs=runtime_inputs,
                context=context,
                completed_blocks=completed_blocks,
                current_wave_index=wave_idx,
                execution_waves=execution_waves,
                pause_exception=e,  # Marks this as pause checkpoint
            )

            # Update exception with saved checkpoint_id and re-raise
            raise ExecutionPaused(
                prompt=e.prompt,
                checkpoint_data={**e.checkpoint_data, "checkpoint_id": checkpoint_id},
            )

    def _execution_to_dict(self, context: Execution) -> dict[str, Any]:
        """Convert Execution model to dict for legacy variable resolution."""
        metadata = (
            context.metadata
            if isinstance(context.metadata, dict)
            else context.metadata.model_dump()
        )
        blocks = {
            block_id: (
                block_exec.model_dump() if isinstance(block_exec, Execution) else block_exec
            )
            for block_id, block_exec in context.blocks.items()
        }
        return {
            "inputs": context.inputs,
            "metadata": metadata,
            "blocks": blocks,
        }

    def _evaluate_condition(self, condition: str, context: Execution) -> bool:
        """Evaluate block condition."""
        try:
            context_dict = self._execution_to_dict(context)
            evaluator = ConditionEvaluator()
            return evaluator.evaluate(condition, context_dict)
        except InvalidConditionError as e:
            raise ValueError(f"Condition evaluation failed: {e}")

    def _resolve_block_inputs(self, inputs: dict[str, Any], context: Execution) -> dict[str, Any]:
        """Resolve variables in block inputs."""
        context_dict = self._execution_to_dict(context)
        resolver = VariableResolver(context_dict)
        resolved: dict[str, Any] = resolver.resolve(inputs)
        return resolved

    def _merge_workflow_inputs(
        self,
        workflow_schema: WorkflowSchema,
        runtime_inputs: dict[str, Any] | None,
    ) -> dict[str, Any]:
        """Merge default and runtime inputs.

        Raises:
            ValueError: If required inputs are missing
        """
        merged = {}

        # Apply defaults
        for input_name, input_decl in workflow_schema.inputs.items():
            if input_decl.default is not None:
                merged[input_name] = input_decl.default

        # Override with runtime inputs
        if runtime_inputs:
            merged.update(runtime_inputs)

        # Validate required inputs
        missing_inputs = []
        empty_string_inputs = []
        for input_name, input_decl in workflow_schema.inputs.items():
            is_required = getattr(input_decl, "required", False)
            if is_required:
                # Check if input is missing
                if input_name not in merged:
                    missing_inputs.append(input_name)
                # Check if required string input is empty (common error case)
                elif input_decl.type.value == "str" and merged[input_name] == "":
                    empty_string_inputs.append(input_name)

        errors = []
        if missing_inputs:
            errors.append(f"Missing required inputs: {', '.join(missing_inputs)}")
        if empty_string_inputs:
            errors.append(
                f"Required string inputs cannot be empty: {', '.join(empty_string_inputs)}"
            )

        if errors:
            raise ValueError("; ".join(errors))

        return merged

    def _evaluate_workflow_outputs(
        self,
        workflow_schema: WorkflowSchema,
        context: Execution,
    ) -> dict[str, Any]:
        """Evaluate workflow-level outputs."""
        if not workflow_schema.outputs:
            return {}

        outputs = {}
        context_dict = self._execution_to_dict(context)
        resolver = VariableResolver(context_dict)
        evaluator = ConditionEvaluator()

        # Comparison operators for boolean expression detection
        comparison_ops = ["==", "!=", ">=", "<=", ">", "<", " and ", " or ", " not "]

        for output_name, output_value in workflow_schema.outputs.items():
            output_expr = output_value if isinstance(output_value, str) else output_value.value

            # Resolve variables
            resolved_value = resolver.resolve(output_expr)

            # Evaluate boolean expressions if present
            is_string = isinstance(resolved_value, str)
            has_operator = (
                any(op in resolved_value for op in comparison_ops) if is_string else False
            )
            if is_string and has_operator:
                try:
                    resolved_value = evaluator.evaluate(resolved_value, context_dict)
                except InvalidConditionError:
                    pass

            outputs[output_name] = resolved_value

        return outputs

    def _execution_to_response(
        self,
        execution: Execution,
        response_format: Literal["minimal", "detailed"],
    ) -> WorkflowResponse:
        """Convert Execution model to WorkflowResponse."""
        # Convert blocks to dict format for response
        blocks_dict = {}
        for block_id, block_exec in execution.blocks.items():
            if isinstance(block_exec, Execution):
                # Nested execution (from ExecuteWorkflow)
                blocks_dict[block_id] = block_exec.model_dump()
            else:
                blocks_dict[block_id] = block_exec

        # Convert metadata to dict if needed
        metadata_dict = (
            execution.metadata
            if isinstance(execution.metadata, dict)
            else execution.metadata.model_dump()
        )

        return WorkflowResponse(
            status="success",
            outputs=execution.outputs,
            blocks=blocks_dict if response_format == "detailed" else {},
            metadata=metadata_dict if response_format == "detailed" else {},
            response_format=response_format,
        )

    async def _save_checkpoint(
        self,
        workflow_name: str,
        workflow_schema: WorkflowSchema,
        runtime_inputs: dict[str, Any],
        context: Execution,
        completed_blocks: list[str],
        current_wave_index: int,
        execution_waves: list[list[str]],
        pause_exception: ExecutionPaused | None = None,
    ) -> str:
        """
        Save workflow checkpoint for crash recovery or pause/resume.

        Args:
            workflow_name: Name of workflow being executed
            workflow_schema: Workflow schema definition
            runtime_inputs: Original runtime inputs
            context: Current execution context (Execution model)
            completed_blocks: List of completed block IDs
            current_wave_index: Index of current wave
            execution_waves: All execution waves
            pause_exception: ExecutionPaused exception (if paused, None for regular checkpoint)

        Returns:
            Checkpoint ID
        """
        from .checkpoint import CheckpointState

        # Generate checkpoint ID
        prefix = "pause" if pause_exception else "chk"
        timestamp = int(time.time() * 1000)
        checkpoint_id = f"{prefix}_{workflow_name}_{timestamp}_{uuid.uuid4().hex[:8]}"

        # Extract workflow stack from internal state
        workflow_stack = context._internal.get("workflow_stack", [])

        # Convert workflow schema blocks to dict for serialization
        block_definitions = {block.id: block.model_dump() for block in workflow_schema.blocks}

        # Extract pause metadata if this is a pause checkpoint
        paused_block_id = None
        pause_prompt = None
        pause_metadata = None

        if pause_exception:
            # Extract paused block ID from checkpoint_data if available
            paused_block_id = pause_exception.checkpoint_data.get("paused_block_id")
            pause_prompt = pause_exception.prompt
            pause_metadata = pause_exception.checkpoint_data

        # Create checkpoint state
        # Convert workflow stack to expected format
        stack_list = (
            [{"name": wf} for wf in workflow_stack]
            if isinstance(workflow_stack, list)
            else []
        )

        checkpoint_state = CheckpointState(
            checkpoint_id=checkpoint_id,
            workflow_name=workflow_name,
            created_at=time.time(),
            runtime_inputs=runtime_inputs,
            context=context,  # Pass Execution directly (no serialization needed)
            completed_blocks=completed_blocks.copy(),
            current_wave_index=current_wave_index,
            execution_waves=execution_waves,
            block_definitions=block_definitions,
            workflow_stack=stack_list,
            paused_block_id=paused_block_id,
            pause_prompt=pause_prompt,
            pause_metadata=pause_metadata,
        )

        # Save checkpoint
        await self.checkpoint_store.save_checkpoint(checkpoint_state)

        logger.info(
            f"Saved {'pause ' if pause_exception else ''}checkpoint '{checkpoint_id}' "
            f"for workflow '{workflow_name}' at wave {current_wave_index}"
        )

        return checkpoint_id

    async def _resume_paused_block(
        self,
        block_id: str,
        block_def: BlockDefinition,
        context: Execution,
        response: str,
        pause_metadata: dict[str, Any],
        wave_idx: int,
        execution_order: int,
    ) -> None:
        """
        Resume a paused block execution.

        Args:
            block_id: Block ID
            block_def: Block definition
            context: Execution context
            response: LLM response to pause prompt
            pause_metadata: Metadata from pause
            wave_idx: Wave index
            execution_order: Execution order

        Raises:
            ExecutionPaused: If block pauses again
        """
        # 1. Resolve variables in inputs (same as normal execution)
        resolved_inputs = self._resolve_block_inputs(block_def.inputs, context)

        # 2. Get executor
        executor = self.registry.get(block_def.type)

        # 3. Create input model
        input_model = executor.input_type(**resolved_inputs)

        # 4. Resume via orchestrator
        block_execution = await self.orchestrator.resume_block(
            executor=executor,
            inputs=input_model,
            context=context,
            response=response,
            pause_metadata=pause_metadata,
            wave=wave_idx,
            execution_order=execution_order,
        )

        # 5. Handle pause (block paused again)
        if block_execution.paused:
            # Add paused_block_id to checkpoint_data (fractal pattern)
            pause_data = block_execution.pause_checkpoint_data or {}
            pause_data["paused_block_id"] = block_id

            raise ExecutionPaused(
                prompt=block_execution.pause_prompt or "Execution paused",
                checkpoint_data=pause_data,
            )

        # 6. Store result
        if block_def.type == "ExecuteWorkflow":
            # Special case: ExecuteWorkflow returns child Execution
            if block_execution.output is None:
                # ExecuteWorkflow failed - create minimal failed Execution
                context.blocks[block_id] = Execution(
                    inputs=resolved_inputs,
                    outputs={},
                    metadata=block_execution.metadata,
                    blocks={},
                )
            else:
                # Wrap child execution with block-level metadata (same as execute path)
                assert isinstance(block_execution.output, Execution)
                child_exec = block_execution.output
                context.blocks[block_id] = Execution(
                    inputs=resolved_inputs,
                    outputs=child_exec.outputs,  # Child workflow outputs
                    metadata=block_execution.metadata,  # Block metadata
                    blocks=child_exec.blocks,  # Preserve child's nested blocks
                )
        else:
            # Regular block: store inputs, outputs, metadata
            context.set_block_result(
                block_id=block_id,
                inputs=resolved_inputs,
                outputs=block_execution.output.model_dump() if block_execution.output else {},
                metadata=block_execution.metadata,
            )

    async def resume_workflow(
        self,
        checkpoint_id: str,
        response: dict[str, Any] | str | None = None,
        response_format: Literal["minimal", "detailed"] = "minimal",
    ) -> WorkflowResponse:
        """
        Resume workflow from checkpoint.

        Args:
            checkpoint_id: Checkpoint ID
            response: LLM response for paused workflows
            response_format: Output verbosity

        Returns:
            WorkflowResponse
        """
        # Convert response to string for internal method
        response_str = (
            response if isinstance(response, str) else str(response or "")
        )

        try:
            # Call internal resume method (returns Execution)
            execution = await self._resume_workflow_internal(checkpoint_id, response_str)

            # Convert to WorkflowResponse
            return self._execution_to_response(execution, response_format)

        except ValueError as e:
            # Checkpoint or workflow not found
            return WorkflowResponse(
                status="failure",
                error=str(e),
                response_format=response_format,
            )

        except ExecutionPaused as e:
            # Workflow paused again - checkpoint already saved in _resume_workflow_internal
            checkpoint_id = e.checkpoint_data.get("checkpoint_id", "")
            return WorkflowResponse(
                status="paused",
                checkpoint_id=checkpoint_id,
                prompt=e.prompt,
                response_format=response_format,
            )

    async def _resume_workflow_internal(
        self,
        checkpoint_id: str,
        response: str | None = None,
    ) -> Execution:
        """Resume workflow from checkpoint (restored context, wave N+1).

        Args:
            checkpoint_id: Checkpoint ID
            response: LLM response for paused workflows

        Returns:
            Execution context

        Raises:
            ExecutionPaused: If workflow pauses again (with checkpoint_id)
            ValueError: If checkpoint or workflow not found, or if resumed block fails
        """
        # 1. Load checkpoint
        checkpoint = await self.checkpoint_store.load_checkpoint(checkpoint_id)
        if checkpoint is None:
            raise ValueError(f"Checkpoint not found: {checkpoint_id}")

        # 2. Get workflow schema
        workflow_name = checkpoint.workflow_name
        if workflow_name not in self.workflows:
            raise ValueError(f"Workflow not found: {workflow_name}")
        workflow_schema = self.workflows[workflow_name]

        # 3. Restore execution context
        context = self._restore_execution_context(checkpoint)

        # 4. Resume paused block if needed
        completed_blocks = checkpoint.completed_blocks.copy()
        if checkpoint.paused_block_id:
            paused_block_id = checkpoint.paused_block_id

            # Get block definition
            if paused_block_id not in checkpoint.block_definitions:
                raise ValueError(f"Paused block not found: {paused_block_id}")
            block_def = BlockDefinition(**checkpoint.block_definitions[paused_block_id])

            # Resume paused block (may raise ExecutionPaused if it pauses again)
            await self._resume_paused_block(
                block_id=paused_block_id,
                block_def=block_def,
                context=context,
                response=response or "",
                pause_metadata=checkpoint.pause_metadata or {},
                wave_idx=checkpoint.current_wave_index,
                execution_order=len(completed_blocks),
            )

            # Verify resumed block succeeded
            resumed_block_metadata = context.get_block_metadata(paused_block_id)
            if resumed_block_metadata and resumed_block_metadata.status.is_failed():
                raise ValueError(
                    f"Failed to resume block '{paused_block_id}': "
                    f"{resumed_block_metadata.message}"
                )

            completed_blocks.append(paused_block_id)

        # 5. Execute remaining waves starting from next wave
        await self._execute_waves_from(
            start_wave_index=checkpoint.current_wave_index + 1,
            execution_waves=checkpoint.execution_waves,
            workflow_name=workflow_name,
            workflow_schema=workflow_schema,
            runtime_inputs=checkpoint.runtime_inputs,
            context=context,
            completed_blocks=completed_blocks,
        )

        # 6. Finalize context (no start_time for resume)
        self._finalize_execution_context(
            workflow_schema, context, completed_blocks, checkpoint.execution_waves
        )

        return context
