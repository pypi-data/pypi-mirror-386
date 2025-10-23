"""Test ExecuteWorkflow with ADR-007 block status shortcuts.

Verifies that ExecuteWorkflow blocks properly wrap child execution results
with block-level metadata, enabling ADR-007 shortcuts like:
- ${blocks.child.succeeded}
- ${blocks.child.failed}
- ${blocks.child.status}
- ${blocks.child.outcome}
"""

import pytest

from workflows_mcp.engine.execution import Execution
from workflows_mcp.engine.executor import WorkflowExecutor
from workflows_mcp.engine.executor_base import create_default_registry
from workflows_mcp.engine.loader import load_workflow_from_yaml


@pytest.fixture
def executor_with_child_workflows():
    """Create executor with child workflows loaded."""
    executor_registry = create_default_registry()
    executor = WorkflowExecutor(registry=executor_registry)

    # Child workflow that succeeds
    child_yaml = """
name: child-success
description: Simple child workflow that succeeds
inputs:
  message:
    type: str
    default: "Hello"
    description: "Message to echo"
blocks:
  - id: echo
    type: Shell
    inputs:
      command: echo "${inputs.message}"
outputs:
  result: "${blocks.echo.outputs.stdout}"
"""
    result = load_workflow_from_yaml(child_yaml)
    assert result.is_success
    executor.load_workflow(result.value)

    # Child workflow that fails
    child_fail_yaml = """
name: child-failure
description: Simple child workflow that fails
blocks:
  - id: fail
    type: Shell
    inputs:
      command: exit 1
outputs:
  result: "failed"
"""
    result = load_workflow_from_yaml(child_fail_yaml)
    assert result.is_success
    executor.load_workflow(result.value)

    return executor


@pytest.mark.asyncio
async def test_execute_workflow_succeeded_shortcut(executor_with_child_workflows):
    """Test ${blocks.child.succeeded} works for ExecuteWorkflow blocks."""
    parent_yaml = """
name: parent-workflow
description: Parent workflow that calls child
blocks:
  - id: call_child
    type: ExecuteWorkflow
    inputs:
      workflow: "child-success"
      inputs:
        message: "Test"
outputs:
  child_succeeded: "${blocks.call_child.succeeded}"
  child_result: "${blocks.call_child.outputs.result}"
"""
    result = load_workflow_from_yaml(parent_yaml)
    assert result.is_success
    executor_with_child_workflows.load_workflow(result.value)

    response = await executor_with_child_workflows.execute_workflow("parent-workflow")

    assert response.status == "success"
    assert response.outputs["child_succeeded"] == "true"
    assert "Test" in response.outputs["child_result"]


@pytest.mark.asyncio
async def test_execute_workflow_failed_shortcut(executor_with_child_workflows):
    """Test ${blocks.child.failed} works when child operation fails.

    Note: ExecuteWorkflow executor always succeeds (returns Execution),
    so the block-level succeeded/failed refers to whether ExecuteWorkflow
    executed, not whether the child workflow's operations succeeded.
    """
    parent_yaml = """
name: parent-with-failing-child
description: Parent workflow that calls failing child
blocks:
  - id: call_child
    type: ExecuteWorkflow
    inputs:
      workflow: "child-failure"
outputs:
  child_succeeded: "${blocks.call_child.succeeded}"
  child_failed: "${blocks.call_child.failed}"
"""
    result = load_workflow_from_yaml(parent_yaml)
    assert result.is_success
    executor_with_child_workflows.load_workflow(result.value)

    response = await executor_with_child_workflows.execute_workflow("parent-with-failing-child")

    assert response.status == "success"  # Parent succeeds
    # ExecuteWorkflow block succeeded (it completed and returned Execution)
    assert response.outputs["child_succeeded"] == "true"
    assert response.outputs["child_failed"] == "false"


@pytest.mark.asyncio
async def test_execute_workflow_status_string(executor_with_child_workflows):
    """Test ${blocks.child.status} returns status string."""
    parent_yaml = """
name: parent-with-status-check
description: Parent workflow checking child status
blocks:
  - id: call_child
    type: ExecuteWorkflow
    inputs:
      workflow: "child-success"
outputs:
  child_status: "${blocks.call_child.status}"
"""
    result = load_workflow_from_yaml(parent_yaml)
    assert result.is_success
    executor_with_child_workflows.load_workflow(result.value)

    response = await executor_with_child_workflows.execute_workflow("parent-with-status-check")

    assert response.status == "success"
    assert response.outputs["child_status"] == "completed"


@pytest.mark.asyncio
async def test_execute_workflow_outcome_string(executor_with_child_workflows):
    """Test ${blocks.child.outcome} returns outcome string."""
    parent_yaml = """
name: parent-with-outcome-check
description: Parent workflow checking child outcome
blocks:
  - id: call_success
    type: ExecuteWorkflow
    inputs:
      workflow: "child-success"

  - id: call_failure
    type: ExecuteWorkflow
    inputs:
      workflow: "child-failure"
    depends_on:
      - call_success
outputs:
  success_outcome: "${blocks.call_success.outcome}"
  failure_outcome: "${blocks.call_failure.outcome}"
"""
    result = load_workflow_from_yaml(parent_yaml)
    assert result.is_success
    executor_with_child_workflows.load_workflow(result.value)

    response = await executor_with_child_workflows.execute_workflow("parent-with-outcome-check")

    assert response.status == "success"
    assert response.outputs["success_outcome"] == "success"
    assert response.outputs["failure_outcome"] == "success"  # ExecuteWorkflow always succeeds


@pytest.mark.asyncio
async def test_execute_workflow_conditional_based_on_status(executor_with_child_workflows):
    """Test conditions using ExecuteWorkflow status shortcuts."""
    parent_yaml = """
name: parent-with-conditional
description: Parent workflow with conditional based on child status
blocks:
  - id: call_child
    type: ExecuteWorkflow
    inputs:
      workflow: "child-success"

  - id: success_handler
    type: Shell
    inputs:
      command: echo "Child succeeded!"
    condition: "${blocks.call_child.succeeded}"
    depends_on:
      - call_child

  - id: failure_handler
    type: Shell
    inputs:
      command: echo "Child failed!"
    condition: "${blocks.call_child.failed}"
    depends_on:
      - call_child
outputs:
  success_ran: "${blocks.success_handler.succeeded}"
  failure_ran: "${blocks.failure_handler.skipped}"
"""
    result = load_workflow_from_yaml(parent_yaml)
    assert result.is_success
    executor_with_child_workflows.load_workflow(result.value)

    response = await executor_with_child_workflows.execute_workflow("parent-with-conditional")

    assert response.status == "success"
    assert response.outputs["success_ran"] == "true"
    assert response.outputs["failure_ran"] == "true"  # Skipped because condition false


@pytest.mark.asyncio
async def test_execute_workflow_preserves_nested_blocks(executor_with_child_workflows):
    """Test that child's nested blocks are preserved for deep access."""
    parent_yaml = """
name: parent-with-deep-access
description: Parent workflow accessing child's nested blocks
blocks:
  - id: call_child
    type: ExecuteWorkflow
    inputs:
      workflow: "child-success"
      inputs:
        message: "Deep"
outputs:
  child_output: "${blocks.call_child.outputs.result}"
  nested_stdout: "${blocks.call_child.blocks.echo.outputs.stdout}"
  nested_status: "${blocks.call_child.blocks.echo.metadata.status}"
"""
    result = load_workflow_from_yaml(parent_yaml)
    assert result.is_success
    executor_with_child_workflows.load_workflow(result.value)

    response = await executor_with_child_workflows.execute_workflow("parent-with-deep-access")

    assert response.status == "success"
    assert "Deep" in response.outputs["child_output"]
    assert "Deep" in response.outputs["nested_stdout"]
    # ADR-007 shortcuts only work at top level, nested requires explicit metadata
    assert response.outputs["nested_status"] == "completed"


@pytest.mark.asyncio
async def test_execute_workflow_metadata_structure(executor_with_child_workflows):
    """Verify ExecuteWorkflow block has proper metadata structure."""
    parent_yaml = """
name: parent-metadata-check
description: Verify metadata structure
blocks:
  - id: call_child
    type: ExecuteWorkflow
    inputs:
      workflow: "child-success"
"""
    result = load_workflow_from_yaml(parent_yaml)
    assert result.is_success
    executor_with_child_workflows.load_workflow(result.value)

    # Execute workflow and get internal execution context
    execution = await executor_with_child_workflows._execute_workflow_internal(
        "parent-metadata-check", {}
    )

    # Verify block structure
    assert "call_child" in execution.blocks
    call_child_block = execution.blocks["call_child"]

    # Should be an Execution object
    assert isinstance(call_child_block, Execution)

    # Should have block-level metadata (not workflow metadata)
    metadata = call_child_block.metadata
    assert hasattr(metadata, "succeeded")
    assert hasattr(metadata, "failed")
    assert hasattr(metadata, "status")
    assert hasattr(metadata, "outcome")

    # Should have child's outputs
    assert "result" in call_child_block.outputs

    # Should have child's nested blocks
    assert "echo" in call_child_block.blocks
