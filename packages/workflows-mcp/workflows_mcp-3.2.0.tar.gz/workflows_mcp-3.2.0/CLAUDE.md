# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an **MCP (Model Context Protocol) server** that exposes DAG-based workflow execution as tools for LLM Agents. The server enables:

- **Workflow-as-Tools**: Complex multi-step workflows exposed as MCP tools
- **Adaptive Orchestration**: Claude can discover and execute workflows dynamically
- **Template-First Architecture**: Reusable workflow patterns for composition
- **Git Integration**: Worktree-based isolation for parallel development

### Current Capabilities

The workflow engine provides comprehensive workflow orchestration:

**Variable Resolution**:

- Use `${var}` syntax with explicit namespace paths
- Reference workflow inputs: `${inputs.field_name}`
- Reference block outputs: `${blocks.block_id.outputs.field}`
- Reference block state (ADR-005 shortcuts): `${blocks.block_id.succeeded|failed|skipped}`
- Reference workflow metadata: `${metadata.field_name}`
- Recursive resolution with nested references
- Example:

  ```yaml
  - id: create_file
    type: CreateFile
    inputs:
      path: "${inputs.workspace}/README.md"
      content: |
        # ${inputs.project_name}
        Version: ${inputs.version}

        Tests Passed: ${blocks.run_tests.succeeded}
        Exit Code: ${blocks.run_tests.outputs.exit_code}
  ```

**Conditional Execution**:

- Add conditions to any block with boolean expressions
- Safe AST evaluation (no arbitrary code execution)
- Access workflow inputs, block outputs, and metadata in conditions
- Example:

  ```yaml
  - id: deploy
    type: ExecuteWorkflow
    inputs:
      workflow: "deploy-production"
    condition: >
      ${blocks.run_tests.outputs.exit_code} == 0 and
      ${inputs.environment} == 'production'
    depends_on: [run_tests]
  ```

**File Operations**:

- **CreateFile**: Create files with content, permissions, encoding
- **ReadFile**: Read text/binary files into workflow context
- **RenderTemplate**: RenderTemplate Jinja2 templates with variables
- Example:

  ```yaml
  - id: populate_readme
    type: RenderTemplate
    inputs:
      template: |
        # {{ project_name }}
        Version: {{ version }}
      variables:
        project_name: "MyApp"
        version: "1.0.0"
  ```

**Workflow Composition**:

- Call workflows as blocks via ExecuteWorkflow
- Multi-level composition support
- Circular dependency detection
- Clean context isolation between parent and child workflows
- Example:

  ```yaml
  - id: ci_pipeline
    type: ExecuteWorkflow
    inputs:
      workflow: "python-ci-pipeline"
      inputs:
        project_path: "${inputs.workspace}"
        python_path: "${blocks.setup.outputs.python_path}"
  ```

**Reusable Workflow Library**:

- Python development workflows (setup-python-env, run-pytest, lint-python)
- Git operation workflows (git-checkout-branch, commit-and-push)
- CI/CD workflows (python-ci-pipeline, conditional-deploy)
- File processing and example workflows

### Code Organization

The workflow engine implementation is in `src/workflows_mcp/engine/` with the MCP server in `src/workflows_mcp/server.py`. All workflow blocks, DAG resolution, variable resolution, and execution logic are part of the main package.

## ADR-005: Success State Architecture (Current Standard)

**Philosophy**: Separate data (outputs) from state (metadata) for clarity and consistency.

### Key Principles

1. **Outputs = Data Only**: Block outputs contain only data produced by operations (exit_code, stdout, file paths, etc.)
2. **Metadata = State + Execution Info**: Block metadata contains state information (`succeeded`, `failed`, `skipped`) and execution details
3. **Execution Always Succeeds**: Blocks return `Result.success()` even if the operation fails (e.g., command exits with code 1)
4. **Operation Outcome in Metadata**: `metadata.operation_succeeded` signals whether the operation succeeded

### Shortcut Accessors

Clean syntax for accessing block state:

```yaml
# Instead of: ${blocks.test.metadata.succeeded}
condition: "${blocks.test.succeeded}"

# Instead of: ${blocks.build.metadata.failed}
condition: "${blocks.build.failed}"

# Instead of: ${blocks.lint.metadata.skipped}
condition: "${blocks.lint.skipped}"
```

### Block Status Values

Each block has a `metadata.status` field with these values:

| Status | Description | `succeeded` | `failed` | `skipped` |
|--------|-------------|------------|---------|----------|
| `success` | Block ran, operation succeeded | `true` | `false` | `false` |
| `failure` | Block ran, operation failed (exit code != 0) | `false` | `true` | `false` |
| `crashed` | Block failed to execute (exception) | `false` | `true` | `false` |
| `skipped` | Block didn't run (condition/dependency) | `false` | `false` | `true` |

### Shell Executor Changes

**Before (with continue-on-error)**:
```yaml
- id: run_tests
  type: Shell
  inputs:
    command: pytest tests/
    continue-on-error: true  # REMOVED in ADR-005
```

**After (check exit_code or use shortcuts)**:
```yaml
- id: run_tests
  type: Shell
  inputs:
    command: pytest tests/

- id: deploy
  type: Shell
  inputs:
    command: ./deploy.sh
  # Option 1: Use shortcut accessor
  condition: "${blocks.run_tests.succeeded}"
  # Option 2: Check exit code explicitly
  # condition: "${blocks.run_tests.outputs.exit_code} == 0"
  depends_on: [run_tests]
```

### Migration Guide

See [docs/ADR-005-MIGRATION-GUIDE.md](docs/ADR-005-MIGRATION-GUIDE.md) for comprehensive migration patterns and examples.

**Quick Reference**:
- Replace `${blocks.*.outputs.success}` → `${blocks.*.succeeded}`
- Remove `continue-on-error: true` from Shell blocks
- Use `${blocks.*.outputs.exit_code}` for explicit exit code checks
- All old patterns remain backward compatible

## MCP Development Principles

### Critical: Always Use Context7 for Library Research

**Before writing any code**, use the Context7 MCP tool to verify:

- Correct library versions and APIs
- Best practices and patterns
- Breaking changes and deprecations
- Official examples and documentation

Example usage:

```text
Use Context7 to research: "mcp python-sdk server implementation patterns"
Use Context7 to research: "pydantic v2 field validation latest"
```

This ensures you're always using current, correct library implementations.

### Official Anthropic Python MCP SDK

**Always use the official Anthropic SDK for MCP development:**

- **Repository**: <https://github.com/modelcontextprotocol/python-sdk>
- **Documentation**: <https://modelcontextprotocol.io/docs/develop/build-server>
- **Project Generator**: `modelcontextprotocol/create-python-server`
- **Contains**: Examples, guides, and best practices for Python MCP servers

**Installation (verified pattern)**:

 ```bash
# Create new project with uv (recommended)
uv init workflows-mcp
cd workflows-mcp
uv add "mcp[cli]"

# Or use the official generator
npx @modelcontextprotocol/create-server workflows-mcp
```python

**Basic Server Pattern (verified from official docs)**:

```python
from mcp.server.fastmcp import FastMCP

# Initialize server
mcp = FastMCP("workflows")

# Define a tool with decorator
@mcp.tool()
async def execute_workflow(workflow_name: str, inputs: dict) -> dict:
    """Execute a workflow with given inputs."""
    # Implementation
    return {"status": "success", "outputs": {}}

# Define a resource
@mcp.resource("workflow://list")
async def list_workflows() -> str:
    """List available workflows."""
    return '["workflow1", "workflow2"]'

# Define a prompt
@mcp.prompt()
def workflow_help(workflow_name: str) -> str:
    """Get help for a workflow."""
    return f"Help for {workflow_name}"

# Entry point for direct execution
def main():
    """Run the server."""
    mcp.run()  # Defaults to stdio transport

if __name__ == "__main__":
    main()
```

**When implementing MCP features:**

1. Use FastMCP built into the official SDK (not standalone FastMCP 2.0)
2. Leverage decorators: `@mcp.tool()`, `@mcp.resource()`, `@mcp.prompt()`
3. Use async functions for all handlers
4. Rely on type hints for automatic schema generation
5. Never write to stdout (use stderr for logging)

### MCP Server Best Practices (Official Guidelines)

**From Official Documentation**:

1. **Logging Rules** (Critical):
   - ⛔ **NEVER write to stdout** - MCP uses stdout for protocol communication
   - ✅ Use logging libraries that write to stderr: `logging`, `loguru`
   - ✅ Configure loggers to use stderr explicitly
   - ⛔ Avoid `print()` statements in production code

2. **Server Structure**:
   - Start simple: single `server.py` file
   - Organize into modules as complexity grows
   - Use decorators for all handlers
   - Keep server initialization minimal

3. **Tool Definitions**:
   - Use type hints for automatic schema generation
   - Write clear docstrings (become tool descriptions)
   - Prefer async functions for I/O operations
   - Return structured data (dicts, dataclasses, Pydantic models)

4. **Error Handling**:
   - Implement robust error handling in tools
   - Provide meaningful error messages
   - Use try-except for external API calls
   - Return error information in tool responses

5. **Development Workflow**:

   ```bash
   # Test during development with MCP Inspector
   uv run mcp dev server.py

   # Add dependencies for development
   uv run mcp dev server.py --with pandas --with numpy

   # Mount local code for live reloading
   uv run mcp dev server.py --with-editable .

   # Install in Claude Desktop
   uv run mcp install server.py

   # Install with custom name
   uv run mcp install server.py --name "My Workflow Server"

   # Install with environment variables
   uv run mcp install server.py -v API_KEY=abc123 -v DB_URL=postgres://...
   uv run mcp install server.py -f .env

   # Run directly
   uv run server.py
   python server.py
   ```

### Official MCP Project Structure

**Verified from**: `modelcontextprotocol/create-python-server` (official project generator)

**Philosophy from Official SDK**: "No configuration or complicated folder structures, only the files you need to run your server"

The official MCP Python SDK recommends a **minimal, simple structure**:

#### Start Simple: Single File Server

For most cases, start with a single `server.py` file:

```text
workflows-mcp/
├── server.py                  # All your tools, resources, prompts in one file
├── pyproject.toml             # uv project config (optional)
└── README.md                  # Documentation (optional)
```

#### Minimal Structure (Official Template)

When you need more organization, use the minimal structure from `create-python-server`:

```text
workflows-mcp/                  # MCP server project root
├── README.md
├── pyproject.toml             # uv-based project config
└── src/
    └── workflows_mcp/
        ├── __init__.py
        ├── __main__.py        # Entry point for uv run
        └── server.py          # Main server implementation
```

**Key principles from official SDK**:

- Start with single file, grow as needed
- Use `uv` for dependency management
- FastMCP is built into the SDK: `from mcp.server.fastmcp import FastMCP`
- Add structure only when complexity demands it

#### For Larger Projects

When your server grows complex, organize within `src/workflows_mcp/`:

```text
src/workflows_mcp/
├── __init__.py
├── __main__.py
├── server.py              # FastMCP initialization
├── tools.py               # Tool definitions (@mcp.tool())
├── resources.py           # Resource handlers (@mcp.resource())
├── prompts.py             # Prompt templates (@mcp.prompt())
└── workflows/             # Workflow engine logic
    ├── executor.py
    ├── dag.py
    └── templates.py
```

**Templates and configuration** (if needed):

```text
workflows-mcp/
├── templates/             # Optional: pre-packaged workflow templates
│   ├── python/
│   ├── node/
│   └── git/
└── tests/                 # Test suite
```

## Core Architecture

### Execution Model

The workflow engine follows a **declarative DAG-based execution model**:

1. **Workflow Definition** (YAML) → blocks with dependencies
2. **DAG Resolution** → topological sort determines execution order
3. **Variable Resolution** → cross-block references resolved from context
4. **Wave Execution** → blocks run in parallel waves based on dependencies
5. **Result Accumulation** → each block's output stored in shared context

## MCP Server Implementation

This project follows official Anthropic MCP Python SDK patterns for robust server implementation.

### Lifespan Management

The server uses lifespan context management for proper resource initialization and cleanup:

```python
@asynccontextmanager
async def app_lifespan(_server: FastMCP) -> AsyncIterator[AppContext]:
    """Manage application lifecycle."""
    # Startup: initialize resources
    registry = WorkflowRegistry()
    executor = WorkflowExecutor()
    load_workflows(registry, executor)

    try:
        yield AppContext(
            registry=registry,
            executor=executor
        )
    finally:
        # Shutdown: cleanup resources
        logger.info("Server shutdown complete")

mcp = FastMCP("workflows", lifespan=app_lifespan)
```

**Key Benefits**:
- ✅ Clean resource initialization on startup
- ✅ Proper cleanup on shutdown
- ✅ Shared resources available to all tools
- ✅ No global mutable state

### Context Injection

All MCP tools use context injection to access shared resources:

```python
@mcp.tool()
async def execute_workflow(
    workflow: str,
    inputs: dict[str, Any] | None = None,
    ctx: Context[ServerSession, AppContext] | None = None,
) -> dict[str, Any]:
    """Execute a workflow with given inputs."""
    # Access shared resources from lifespan context
    app_ctx = ctx.request_context.lifespan_context
    executor = app_ctx.executor
    registry = app_ctx.registry

    # Execute with shared resources
    response = await executor.execute_workflow(workflow, inputs)
    return response.model_dump()
```

**Pattern Benefits**:
- ✅ Type-safe access to shared resources
- ✅ No dependency injection framework needed
- ✅ Clean separation of concerns
- ✅ Easy to test with mock contexts

### Input Validation

All tools validate inputs before execution:

**Workflow Existence Validation**:
```python
# Check workflow exists before execution
if workflow not in registry.list_workflows():
    return {
        "error": f"Workflow '{workflow}' not found",
        "available_workflows": registry.list_workflows(),
        "help": "Use list_workflows() to see all available workflows"
    }
```

**Required Input Validation**:
```python
# Validate required inputs against schema
workflow_def = registry.get_workflow(workflow)
required_inputs = [
    name for name, spec in workflow_def.inputs.items()
    if spec.required and spec.default is None
]

missing = [inp for inp in required_inputs if inp not in provided_inputs]
if missing:
    return {
        "error": f"Missing required inputs: {missing}",
        "required": required_inputs,
        "help": "Use get_workflow_info() to see input requirements"
    }
```

**Benefits**:
- ✅ Clear error messages with helpful guidance
- ✅ Fail fast before expensive operations
- ✅ Improved user experience

### Error Handling

Consistent error response structure across all tools:

**Execution Errors** (using `WorkflowResponse`):
```python
try:
    result = await executor.execute_workflow(workflow, inputs)
    return result.model_dump()  # status: "success" | "failure"
except Exception as e:
    logger.exception("Workflow execution failed")
    return WorkflowResponse(
        status="failure",
        error=str(e),
        outputs={},
        blocks={},
        metadata={}
    ).model_dump()
```

**Info/Validation Errors**:
```python
# Consistent dict format for non-execution errors
return {
    "error": "Detailed error message",
    "available_options": [...],
    "help": "Suggestion for how to resolve"
}
```

**Context Validation**:
```python
# All tools check for context availability
if ctx is None:
    return {
        "error": "Server context not available",
        "help": "This tool requires server context to access resources"
    }
```

**Benefits**:
- ✅ Predictable error structure for clients
- ✅ Actionable error messages
- ✅ Graceful degradation
- ✅ Comprehensive logging for debugging

### Key Components

**Core Engine** (`src/workflows_mcp/engine/`):

- `executor.py`: Workflow execution orchestrator (ADR-006 unified execution model)
- `orchestrator.py`: BlockOrchestrator for exception handling and metadata creation
- `execution.py`: Fractal execution context model
- `metadata.py`: Execution state and operation outcome tracking
- `dag.py`: Dependency resolution via Kahn's algorithm, parallel wave detection
- `block.py`: BlockInput/BlockOutput Pydantic base classes for executor I/O
- `load_result.py`: LoadResult monad for safe loader/registry file operations
- `variables.py`: Variable resolution and condition evaluation
- `schema.py`: YAML workflow schema definitions
- `loader.py`: Workflow loading from YAML files
- `registry.py`: Workflow registration and discovery

**Executor System** (`src/workflows_mcp/engine/`):

- `executors_core.py`: Shell and ExecuteWorkflow executors
- `executors_file.py`: File operations (CreateFile, ReadFile, RenderTemplate)
- `executors_interactive.py`: Interactive executor (Prompt - simplified single interactive type)
- `executors_state.py`: JSON state management executors
- `executor_base.py`: BlockExecutor base class and EXECUTOR_REGISTRY

**Entry Points**:

- `__main__.py`: CLI entry point for running the MCP server
- `server.py`: FastMCP server initialization
- `tools.py`: MCP tool implementations (execute_workflow, list_workflows, get_workflow_info)

### Variable Substitution System

The workflow engine uses a **four-namespace architecture** that aligns with industry standards (GitHub Actions, Tekton, Argo Workflows). Variable references use explicit namespace paths for clarity and security.

**Four Root-Level Namespaces:**

1. **`inputs`**: Workflow input parameters
2. **`metadata`**: Workflow metadata (name, timestamps, execution info)
3. **`blocks`**: Block execution results (each block has inputs/outputs/metadata)
4. **`__internal__`**: System state (not accessible via variables, security boundary)

**Variable Syntax:**

```yaml
# Workflow inputs
${inputs.project_name}
${inputs.workspace}

# Workflow metadata
${metadata.workflow_name}
${metadata.start_time}

# Block outputs (explicit)
${blocks.create_worktree.outputs.worktree_path}
${blocks.run_tests.outputs.exit_code}

# Block outputs (shortcut - auto-expands to outputs)
${blocks.run_tests.exit_code}           # Same as outputs.exit_code
${blocks.create_worktree.worktree_path}  # Same as outputs.worktree_path

# Block inputs (for debugging)
${blocks.run_tests.inputs.command}

# Block metadata
${blocks.run_tests.metadata.execution_time_ms}
```

**Complete Example:**

```yaml
name: build-project
description: Build project with tests

inputs:
  project_name:
    type: string
    default: "my-project"

  workspace:
    type: string
    default: "."

blocks:
  - id: create_worktree
    type: CreateWorktree
    inputs:
      branch: "feature/${inputs.project_name}"
      path: ".worktrees/${inputs.project_name}"

  - id: create_file
    type: CreateFile
    inputs:
      path: "${blocks.create_worktree.outputs.worktree_path}/README.md"
      content: |
        # ${inputs.project_name}
        Built at: ${metadata.start_time}
    depends_on:
      - create_worktree

  - id: run_tests
    type: Shell
    inputs:
      command: "pytest tests/"
      working_dir: "${blocks.create_worktree.outputs.worktree_path}"
    depends_on:
      - create_file

outputs:
  worktree_path: "${blocks.create_worktree.outputs.worktree_path}"
  tests_passed: "${blocks.run_tests.succeeded}"  # ADR-007: Use shortcut
```

The engine resolves variables during execution by traversing the four-namespace context structure.

### Block Status References (ADR-007)

The workflow engine provides three tiers of status references, aligned with industry standards from GitHub Actions and Argo Workflows:

**Tier 1: Boolean Shortcuts (GitHub Actions Style)** - Use for 90% of cases:

```yaml
# Simple success/failure checks
condition: "${blocks.run_tests.succeeded}"   # True if completed successfully
condition: "${blocks.build.failed}"          # True if failed (any reason)
condition: "${blocks.optional.skipped}"      # True if skipped

# Workflow outputs
outputs:
  tests_passed: "${blocks.run_tests.succeeded}"
  deployment_failed: "${blocks.deploy.failed}"
```

**Tier 2: Status String (Argo Workflows Style)** - Use for precise control:

```yaml
# Check if executor finished (regardless of success)
condition: "${blocks.build.status} == 'completed'"

# Run cleanup if finished OR skipped
condition: "${blocks.test.status} in ['completed', 'skipped']"

# Detect executor crash specifically
condition: "${blocks.parse.status} == 'failed'"
```

**Status values**: `"pending"`, `"running"`, `"completed"`, `"failed"`, `"skipped"`, `"paused"`

**Tier 3: Outcome String (Precision)** - Use to distinguish crash from failure:

```yaml
# Operation failed (executor ran, operation failed)
condition: >
  ${blocks.build.status} == 'completed' and
  ${blocks.build.outcome} == 'failure'

# Executor crashed (couldn't run)
condition: >
  ${blocks.build.status} == 'failed' and
  ${blocks.build.outcome} == 'n/a'
```

**Outcome values**: `"success"`, `"failure"`, `"n/a"`

**Decision Tree** (which tier to use):

```bash
Need to check block status?
├─ "Did it work?" → ${blocks.id.succeeded}       (Tier 1)
├─ "Did it fail?" → ${blocks.id.failed}          (Tier 1)
├─ "Was it skipped?" → ${blocks.id.skipped}      (Tier 1)
│
├─ "Did executor finish?" → ${blocks.id.status} == 'completed'  (Tier 2)
├─ "Run if finished or skipped?" → ${blocks.id.status} in ['completed', 'skipped']  (Tier 2)
│
└─ "Distinguish crash from failure?" → Check both .status and .outcome  (Tier 3)
```

**Common Patterns:**

```yaml
# Deploy only if tests succeeded
- id: deploy
  type: Shell
  inputs:
    command: ./deploy.sh
  condition: "${blocks.run_tests.succeeded}"
  depends_on: [run_tests]

# Cleanup after build (success OR failure)
- id: cleanup
  type: Shell
  inputs:
    command: rm -rf build-cache/
  condition: "${blocks.build.status} == 'completed'"
  depends_on: [build]

# Notify about infrastructure failures
- id: alert_infra_team
  type: Shell
  inputs:
    command: ./alert.sh "Executor crashed"
  condition: "${blocks.deploy.status} == 'failed'"
  depends_on: [deploy]
```

**See**: `docs/ADR-007-BLOCK-STATUS-REFERENCES.md` for complete specification and industry alignment.

## Development Commands

### Testing

Run the comprehensive test suite (86 tests, 48% coverage):

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=workflows_mcp --cov-report=term-missing

# Run specific test files
uv run pytest tests/test_server.py -v      # MCP tool integration (37 tests)
uv run pytest tests/test_executor.py -v    # Workflow execution (24 tests)
uv run pytest tests/test_dag.py -v         # DAG resolution (25 tests)

# Coverage HTML report
uv run pytest --cov=workflows_mcp --cov-report=html
open htmlcov/index.html
```

### Code Quality

The project uses standard Python development tools:

```bash
# Type checking (strict mode)
uv run mypy src/workflows_mcp/

# Linting
uv run ruff check src/workflows_mcp/

# Formatting
uv run ruff format src/workflows_mcp/
```

## Adding New Block Executors

Pattern for creating workflow block executors using the executor pattern:

1. **Create Input/Output models** using Pydantic:

```python
class MyBlockInput(BlockInput):
    """Input schema with strict validation (extra='forbid')."""
    param: str = Field(description="Parameter description")

class MyBlockOutput(BlockOutput):
    """Output schema allowing extra fields (extra='allow')."""
    result: str
    success: bool
```

2. **Implement BlockExecutor** (ADR-006 pattern):

```python
from .execution import Execution

class MyBlockExecutor(BlockExecutor):
    """Stateless executor implementing block logic."""

    type_name = "MyBlock"  # Block type identifier
    input_type = MyBlockInput  # Input schema
    output_type = MyBlockOutput  # Output schema

    async def execute(
        self, inputs: BlockInput, context: Execution
    ) -> MyBlockOutput:
        """Execute block logic (ADR-006: returns BaseModel directly).

        Args:
            inputs: Validated MyBlockInput instance
            context: Execution context (fractal model)

        Returns:
            MyBlockOutput on success

        Raises:
            Exception: Any exception indicates execution failure
        """
        assert isinstance(inputs, MyBlockInput)
        # Implement block logic
        # Return output directly (no Result wrapper)
        return MyBlockOutput(result="...", success=True)
```

3. **Auto-register via module import** (`src/workflows_mcp/engine/__init__.py`):

```python
# Import executor modules to auto-register
from . import (
    executors_core,  # Shell, ExecuteWorkflow
    executors_file,  # CreateFile, ReadFile, RenderTemplate
    # ... your new executor module
)
```

4. **Use in workflows**:

```yaml
blocks:
  - id: my_block
    type: MyBlock  # Matches executor.type_name
    inputs:
      param: "value"
```

Executors auto-register when their module is imported by the engine.

## Critical Design Patterns (ADR-006)

### Executor Return Pattern

**Executors return BaseModel directly** (ADR-006) - no wrapper classes:

```python
async def execute(self, inputs: MyInput, context: Execution) -> MyOutput:
    """
    Returns output directly on success.
    Raises exceptions for failures - caught by BlockOrchestrator.
    """
    # Execute logic
    result = await some_operation()

    # Return typed output directly
    return MyOutput(data=result, success=True)
```

**BlockOrchestrator** handles exceptions and creates Metadata:
- Catches exceptions → Metadata with status=FAILED
- ExecutionPaused exception → Workflow pause
- Success → Metadata with status=COMPLETED

### LoadResult for Loader Layer

**LoadResult** is used exclusively by loader/registry for safe file operations:

```python
from workflows_mcp.engine.load_result import LoadResult

# Loading workflows
load_result = load_workflow_from_file(path)
if load_result.is_success:
    schema = load_result.value
else:
    print(f"Load error: {load_result.error}")

# LoadStatus: SUCCESS or FAILED
```

**Not used by executors** - executors return BaseModel directly per ADR-006.

### Dependency Declaration

Blocks explicitly declare dependencies via `depends_on`:

```yaml
blocks:
  - id: step1
    type: SomeBlock

  - id: step2
    type: AnotherBlock
    depends_on:
      - step1  # step2 waits for step1
```

The DAGResolver validates and orders execution automatically.

### Git Worktree Pattern

The system extensively uses git worktrees for isolation:

```yaml
- id: create_worktree
  type: CreateWorktree
  inputs:
    path: ".worktrees/feature/${inputs.feature_name}"
    branch: "feature/${inputs.feature_name}"
    base_branch: "main"

# Use worktree path in subsequent blocks
- id: create_file
  type: CreateFile
  inputs:
    path: "${blocks.create_worktree.outputs.worktree_path}/new-file.txt"
    content: |
      Feature: ${inputs.feature_name}
      Created at: ${metadata.start_time}
  depends_on:
    - create_worktree
```

## MCP Protocol Compliance

This project strictly adheres to MCP protocol requirements for reliable communication between server and clients.

### Critical Requirements

**Logging to stderr only**:
- ✅ All logging configured to `sys.stderr`
- ⛔ No `print()` statements to stdout (breaks MCP protocol)
- ✅ Use `logger.info()`, `logger.debug()`, etc.

**Rationale**: MCP uses stdout for JSON-RPC protocol messages. Any output to stdout corrupts the communication channel.

**Type Safety**:
- ✅ Strict mypy configuration enabled
- ✅ Pydantic v2 models for all data structures
- ✅ Type hints required for all functions

**Rationale**: Type safety prevents runtime errors and enables FastMCP to auto-generate correct tool schemas.

**Resource Management**:
- ✅ Lifespan context manager for startup/shutdown
- ✅ Proper cleanup of checkpoint store
- ✅ No global mutable state

**Rationale**: Clean resource management prevents leaks and ensures predictable server behavior.

**Tool Schema Generation**:
- ✅ FastMCP auto-generates schemas from type hints
- ✅ Docstrings become tool descriptions
- ⛔ No redundant Pydantic models for tool I/O

**Rationale**: Single source of truth for tool signatures reduces maintenance and prevents schema drift.

### Compliance Verification

**Pre-commit checks**:
```bash
# Verify no stdout usage
rg 'print\(' src/workflows_mcp/ --type py

# Type checking passes
mypy src/workflows_mcp/

# All tests pass
pytest tests/
```

**Runtime verification**:
```bash
# Test with MCP Inspector
uv run mcp dev src/workflows_mcp/server.py

# Verify JSON-RPC communication
# Check stderr only contains logs, stdout only contains protocol messages
```

## System Architecture

See `ARCHITECTURE.md` for comprehensive system architecture documentation including:

- Core component design (DAGResolver, WorkflowExecutor, BlockExecutor pattern)
- Workflow execution model and parallel wave execution
- Variable resolution system
- Conditional execution
- Workflow composition patterns
- Executor system architecture
- MCP integration
- Security model
- Error handling patterns

Also see:
- `docs/adr/ADR-001-executor-pattern-redesign.md` - Original executor pattern design
- `docs/adr/ADR-004-workflowblock-to-executor-migration.md` - Migration from WorkflowBlock to executor pattern

## Project Conventions

### MCP Development Standards

- **Python 3.12+** minimum version
- **uv for package management** - Fast, reliable Python package installer
- **Official Anthropic MCP SDK** - From <https://github.com/modelcontextprotocol/python-sdk>
- **Context7 for research** - Always verify library versions and APIs before coding
- **Pydantic v2** for all input/output validation
- **Type hints required** for all functions
- **Async/await patterns** - Follow SDK async examples

### General Standards

- **Git conventional commits** for semantic versioning
- **Worktree-based development** for isolated feature work
- **YAGNI principle** - Don't build features until needed
- **Templates over custom code** - Favor reusable workflow templates
- **MCP protocol compliance** - All tools must follow MCP specifications

### Custom Workflow Templates

Users can extend the workflow library with custom templates:

**Configuration**:

```bash
export WORKFLOWS_TEMPLATE_PATHS="~/my-workflows,/opt/team-workflows"
```

Or in `.mcp.json`:

```json
{
  "mcpServers": {
    "workflows": {
      "command": "uvx",
      "args": ["--from", "workflows-mcp", "workflows-mcp"],
      "env": {
        "WORKFLOWS_TEMPLATE_PATHS": "~/my-workflows,/opt/team-workflows"
      }
    }
  }
}
```

**Priority System**:

- Built-in templates load first
- User templates override built-in templates by name
- Later directories override earlier directories

**Use Cases**:

- **Personal customizations**: `~/my-workflows/`
- **Team-specific workflows**: `/opt/company-workflows/`
- **Override built-in**: Create `~/my-workflows/python-ci-pipeline.yaml` to replace built-in

**Source Tracking**: Use `WorkflowRegistry.get_workflow_source(name)` to see where each workflow came from

## Testing Strategy

The project maintains comprehensive test coverage with focus on critical paths and integration points.

### Test Coverage (48% overall, 86 tests)

**High Coverage (>80%)**:
- `dag.py`: 98% - Critical path DAG resolution
- `checkpoint.py`: 100% - Checkpoint state management
- `blocks_example.py`: 93% - Test fixtures

**Medium Coverage (50-80%)**:
- `server.py`: 67% - MCP tool implementations
- `executor.py`: 54% - Workflow execution core
- `schema.py`: 72% - YAML schema validation

**Test Organization**:
- `test_dag.py`: DAG resolution and wave computation (25 tests)
- `test_executor.py`: Workflow execution orchestration (24 tests)
- `test_server.py`: MCP tool integration (37 tests)
- Other: Executor modules, schema generation, plugins (existing tests)

### Test Principles

**Arrange-Act-Assert Pattern**:
```python
def test_workflow_execution():
    # Arrange: Set up test data and mocks
    workflow_def = WorkflowDefinition(...)
    inputs = {"param": "value"}

    # Act: Execute the operation
    result = executor.execute_workflow(workflow_def, inputs)

    # Assert: Verify expected outcomes
    assert result.status == "success"
    assert result.outputs["key"] == "expected_value"
```

**Mock External Dependencies**:
- Filesystem operations mocked in unit tests
- Network calls stubbed with predictable responses
- Time-dependent logic controlled via freezegun

**Focus Areas**:
- **Critical Paths**: DAG resolution, workflow execution, variable resolution
- **Error Handling**: Invalid inputs, missing workflows, execution failures
- **Integration**: MCP tools with real workflow engine components

**Performance**:
- Full test suite completes in < 3 seconds
- No external service dependencies
- Parallel test execution enabled

### Coverage Goals

**Priority Areas for Improvement**:
1. `executor.py` (54% → 80%): Add tests for edge cases in wave execution
2. `executors_*.py`: Increase coverage of error paths and edge cases
3. `loader.py`: Test error handling for malformed YAML workflows

**Maintenance Strategy**:
- New features require corresponding tests
- Bug fixes include regression tests
- Coverage tracked in CI/CD pipeline

## File Organization

Current project structure:

```text
src/workflows_mcp/
├── __init__.py              # Package initialization
├── __main__.py              # Entry point (uv run workflows-mcp)
├── server.py                # FastMCP server initialization
├── tools.py                 # MCP tool implementations
├── context.py               # AppContext for lifespan management
├── templates/               # Built-in workflow templates
│   ├── ci/                  # CI/CD workflows
│   ├── examples/            # Tutorial workflows
│   ├── files/               # File processing
│   ├── git/                 # Git operations
│   ├── node/                # Node.js workflows
│   └── python/              # Python workflows
└── engine/                  # Workflow engine
    ├── __init__.py          # Engine exports (imports executors for registration)
    ├── dag.py               # DAG dependency resolution
    ├── load_result.py       # LoadResult monad for loader/registry layer
    ├── block.py             # BlockInput/BlockOutput base classes
    ├── block_status.py      # ExecutionStatus & OperationOutcome enums
    ├── execution.py         # Execution context model (fractal/recursive)
    ├── metadata.py          # Execution metadata
    ├── orchestrator.py      # BlockOrchestrator (exception handling)
    ├── executor_base.py     # BlockExecutor base class & EXECUTOR_REGISTRY
    ├── executor_workflow.py # ExecuteWorkflow executor (ADR-006)
    ├── executors_core.py    # Shell executor
    ├── executors_file.py    # File operation executors
    ├── executors_interactive.py  # Interactive executors
    ├── executors_state.py   # JSON state management executors
    ├── block_utils.py       # Block utility functions
    ├── variables.py         # Variable resolution & conditionals
    ├── executor.py          # WorkflowExecutor (orchestrator)
    ├── response.py          # WorkflowResponse model
    ├── schema.py            # YAML workflow schema
    ├── loader.py            # YAML workflow loader
    ├── registry.py          # Workflow registry
    ├── checkpoint.py        # Checkpoint state management
    └── exceptions.py        # ExecutionPaused exception
```

## Important Implementation Notes (ADR-006)

- **No wrapper classes**: Executors return BaseModel directly, raise exceptions for failures
- **BlockOrchestrator pattern**: Wraps executor calls, catches exceptions, creates Metadata
- **Execution context**: Fractal/recursive model (same structure for workflows and blocks)
- **Executors are stateless**: Singleton pattern, no shared state between executions
- **Metadata separation**: status (execution lifecycle) separate from outcome (operation result)
- **ExecutionStatus**: PENDING, RUNNING, COMPLETED, FAILED, SKIPPED, PAUSED
- **OperationOutcome**: SUCCESS, FAILURE, NOT_APPLICABLE
- **LoadResult**: Used only by loader/registry layer for safe file I/O
- **Variable resolution is lazy**: Variables resolved at execution time, not load time
- **Cyclic dependencies fail fast**: DAG resolver detects cycles before execution starts
- **Wave execution**: Blocks in the same dependency wave execute in parallel
- **Auto-registration**: Executors auto-register via module imports in `engine/__init__.py`

## When Working on This Project

### MCP Development (Primary Focus)

1. **Use Context7 FIRST** - Before any code, research libraries and patterns via Context7 MCP tool
2. **Follow Anthropic Python MCP SDK** - Use official SDK from <https://github.com/modelcontextprotocol/python-sdk>
3. **Read ARCHITECTURE.md** for strategic context and MCP roadmap
4. **MCP-compliant implementations** - Tools, resources, and prompts must follow MCP specifications
5. **Type safety** - Pydantic models for all MCP tool inputs/outputs
6. **Async-first** - Use async/await patterns from SDK examples
7. **Templates over custom code** - Favor reusable workflow templates
