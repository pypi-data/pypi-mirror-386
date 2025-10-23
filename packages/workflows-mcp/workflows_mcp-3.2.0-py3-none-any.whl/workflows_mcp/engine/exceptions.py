"""Workflow execution exceptions for ADR-006 unified execution model."""

from __future__ import annotations

from typing import Any


class ExecutionPaused(Exception):  # noqa: N818
    # Not an error - control flow mechanism (like StopIteration)
    """
    Workflow execution paused for external input.

    This is NOT an error - it's a control flow mechanism for interactive workflows.
    Similar to how StopIteration controls iterator flow in Python.

    When raised by an executor (e.g., Prompt block), it signals that:
    1. Execution cannot continue without external input
    2. Workflow should checkpoint and return to caller
    3. Resume will be called later with LLM response

    The orchestrator catches this exception and:
    - Creates Metadata.from_paused()
    - Stores checkpoint with pause data
    - Returns WorkflowResponse with status="paused"

    MCP Flow:
        1. Prompt block raises ExecutionPaused
        2. Exception bubbles through call stack (nested workflows included)
        3. Orchestrator catches → creates checkpoint → returns to MCP client
        4. LLM receives pause prompt
        5. LLM calls resume_workflow tool with checkpoint_id + response
        6. Workflow resumes from checkpoint

    Attributes:
        prompt: Message/question to present to LLM
        checkpoint_data: Data needed to resume execution (block inputs, state, etc.)
    """

    def __init__(self, prompt: str, checkpoint_data: dict[str, Any]):
        """
        Initialize pause exception.

        Args:
            prompt: Message/question for LLM (e.g., "Approve deployment to production?")
            checkpoint_data: Serializable data for resume (block inputs, context state)
        """
        self.prompt = prompt
        self.checkpoint_data = checkpoint_data
        super().__init__(f"Execution paused: {prompt}")

    def __repr__(self) -> str:
        """Developer-friendly representation."""
        return f"ExecutionPaused(prompt={self.prompt!r})"
