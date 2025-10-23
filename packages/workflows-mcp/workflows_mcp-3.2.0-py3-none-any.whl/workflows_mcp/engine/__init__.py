"""Workflow engine core components using executor pattern.

This package contains the modern workflow execution engine based on the executor pattern.

Key Components (Post ADR-006):

- WorkflowExecutor: Async workflow orchestrator (unified execution model)
- BlockOrchestrator: Exception handling and metadata creation
- BlockExecutor: Base class for executor implementations
- BlockInput/BlockOutput: Pydantic v2 base classes for I/O validation
- Execution: Fractal execution context model
- Metadata: Execution state tracking
- DAGResolver: Dependency resolution via Kahn's algorithm
- WorkflowRegistry: Registry for managing workflow definitions
- WorkflowSchema: Pydantic v2 schema for YAML validation
- LoadResult: Error monad for loader/registry safe file operations

Architecture (ADR-006):
- Executors return BaseModel directly (no wrapper classes)
- Exceptions for control flow (ExecutionPaused for pause)
- BlockOrchestrator wraps executor calls with exception handling
- Execution model provides fractal context (supports nested workflows)
- Plugin System: Executors can be discovered via entry points
- Security Model: Per-executor capabilities and security levels
- Type Safety: Pydantic models ensure correct I/O
"""

# Import executors (they auto-register in create_default_registry)
from . import (  # noqa: F401
    executor_workflow,  # ExecuteWorkflow executor (ADR-006)
    executors_core,  # Shell executor
    executors_file,  # File operation executors
    executors_interactive,  # Interactive executors
    executors_state,  # JSON state executors
)
from .block import BlockInput, BlockOutput
from .dag import DAGResolver
from .executor import WorkflowExecutor
from .executor_base import create_default_registry
from .executor_workflow import (
    ExecuteWorkflowExecutor,
    ExecuteWorkflowInput,
)
from .executors_core import (
    ShellExecutor,
    ShellInput,
    ShellOutput,
)
from .executors_file import (
    CreateFileExecutor,
    CreateFileInput,
    CreateFileOutput,
    RenderTemplateExecutor,
    RenderTemplateInput,
    RenderTemplateOutput,
    ReadFileExecutor,
    ReadFileInput,
    ReadFileOutput,
)
from .executors_interactive import (
    PromptExecutor,
    PromptInput,
    PromptOutput,
)
from .executors_state import (
    MergeJSONStateExecutor,
    MergeJSONStateInput,
    MergeJSONStateOutput,
    ReadJSONStateExecutor,
    ReadJSONStateInput,
    ReadJSONStateOutput,
    WriteJSONStateExecutor,
    WriteJSONStateInput,
    WriteJSONStateOutput,
)
from .load_result import LoadResult
from .loader import load_workflow_from_yaml
from .registry import WorkflowRegistry
from .response import WorkflowResponse
from .schema import WorkflowSchema

__all__ = [
    # Core types
    "LoadResult",
    "DAGResolver",
    "BlockInput",
    "BlockOutput",
    "create_default_registry",
    "WorkflowExecutor",
    "WorkflowRegistry",
    "WorkflowResponse",
    "WorkflowSchema",
    "load_workflow_from_yaml",
    # Core Executors
    "ShellExecutor",
    "ShellInput",
    "ShellOutput",
    "ExecuteWorkflowExecutor",
    "ExecuteWorkflowInput",
    # File Executors
    "CreateFileExecutor",
    "CreateFileInput",
    "CreateFileOutput",
    "ReadFileExecutor",
    "ReadFileInput",
    "ReadFileOutput",
    "RenderTemplateExecutor",
    "RenderTemplateInput",
    "RenderTemplateOutput",
    # Interactive Executors
    "PromptExecutor",
    "PromptInput",
    "PromptOutput",
    # State Executors
    "ReadJSONStateExecutor",
    "ReadJSONStateInput",
    "ReadJSONStateOutput",
    "WriteJSONStateExecutor",
    "WriteJSONStateInput",
    "WriteJSONStateOutput",
    "MergeJSONStateExecutor",
    "MergeJSONStateInput",
    "MergeJSONStateOutput",
]
