"""Test nested variable resolution with Execution models (ADR-006)."""

from workflows_mcp.engine.execution import Execution
from workflows_mcp.engine.metadata import Metadata
from workflows_mcp.engine.variables import VariableResolver


def test_nested_execution_to_dict_conversion():
    """Test that nested Executions convert properly for variable resolution."""
    # Create a nested execution structure (mimics ExecuteWorkflow result)
    child_execution = Execution(
        inputs={"param": "value"},
        outputs={"result": "child_result", "count": 42},
        metadata=Metadata.from_success(
            execution_time_ms=100.0,
            started_at="2025-01-21T10:00:00Z",
            completed_at="2025-01-21T10:00:01Z",
        ),
        blocks={},
    )

    parent_execution = Execution(
        inputs={"workflow": "child-workflow"},
        outputs={"workflow_result": "success"},
        metadata={},
        blocks={
            "child_block": child_execution,  # Nested Execution
        },
    )

    # Convert to dict (simulates what executor does)
    context_dict = {
        "inputs": parent_execution.inputs,
        "metadata": (
            parent_execution.metadata
            if isinstance(parent_execution.metadata, dict)
            else parent_execution.metadata.model_dump()
        ),
        "blocks": {
            block_id: (
                block_exec.model_dump()
                if isinstance(block_exec, Execution)
                else block_exec
            )
            for block_id, block_exec in parent_execution.blocks.items()
        },
    }

    # Test variable resolution with nested path
    resolver = VariableResolver(context_dict)

    # Should resolve nested outputs
    result1 = resolver.resolve("${blocks.child_block.outputs.result}")
    assert result1 == "child_result"

    result2 = resolver.resolve("${blocks.child_block.outputs.count}")
    assert result2 == "42"

    # Should resolve nested metadata
    status = resolver.resolve("${blocks.child_block.metadata.status}")
    assert status == "completed"


def test_deeply_nested_execution_workflow():
    """Test deeply nested ExecuteWorkflow (grandchild) variable resolution."""
    # Grandchild execution
    grandchild = Execution(
        outputs={"final_value": 123},
        metadata={},
        blocks={},
    )

    # Child execution with grandchild
    child = Execution(
        outputs={"child_output": "test"},
        metadata={},
        blocks={"grandchild_block": grandchild},
    )

    # Parent execution
    parent = Execution(
        outputs={},
        metadata={},
        blocks={"child_workflow": child},
    )

    # Convert to dict
    context_dict = {
        "inputs": {},
        "metadata": {},
        "blocks": {
            block_id: (
                block_exec.model_dump()
                if isinstance(block_exec, Execution)
                else block_exec
            )
            for block_id, block_exec in parent.blocks.items()
        },
    }

    # Test deep nested access
    resolver = VariableResolver(context_dict)
    result = resolver.resolve(
        "${blocks.child_workflow.blocks.grandchild_block.outputs.final_value}"
    )
    assert result == "123"
