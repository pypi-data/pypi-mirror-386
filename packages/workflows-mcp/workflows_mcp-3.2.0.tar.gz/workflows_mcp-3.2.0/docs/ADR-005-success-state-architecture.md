# ADR-005: Success State Architecture Redesign

**Status**: Approved
**Date**: 2025-10-20
**Deciders**: Product Owner, Senior Python Developer

## Context

The current architecture has three overlapping concepts of "success":
1. `Result.state` (SUCCESS/FAILED/PAUSED)
2. `context["blocks"]["id"]["metadata"]["status"]` ("success"/"failure"/"skipped")
3. `context["blocks"]["id"]["outputs"]["success"]` (bool - only some executors)

This causes confusion, especially with `continue-on-error` semantics in Shell executor.

## Decision

**Core Principle**: Separate data from state

### 1. Outputs = Data Only (No State)

```python
context["blocks"]["id"]["outputs"] = {
    # Operation data ONLY
    "exit_code": 0,
    "stdout": "...",
    "stderr": "...",
    # NO success, failed, error fields
}
```

### 2. Metadata = State + Execution Info

```python
context["blocks"]["id"]["metadata"] = {
    # Execution timing
    "execution_time_ms": 123.4,
    "started_at": "2025-10-20T10:30:00Z",
    "completed_at": "2025-10-20T10:30:01Z",

    # Status (detailed string)
    "status": "success",  # or failure, skipped, paused

    # Boolean accessors (convenience)
    "succeeded": True,
    "failed": False,
    "skipped": False,

    # Error info (if failed)
    "error": None,
}
```

### 3. Variable Syntax

```yaml
# Shortcut (variable resolver checks metadata first)
condition: ${blocks.test.succeeded}   # Cleaner!
condition: ${blocks.test.failed}
condition: ${blocks.test.skipped}

# Explicit (also supported)
condition: ${blocks.test.metadata.succeeded}
condition: ${blocks.test.metadata.error}
```

### 4. Remove continue-on-error

Shell blocks no longer need `continue-on-error`. Execution always succeeds; operation outcome reflected in `metadata.succeeded`.

```yaml
# Before
- id: test
  type: Shell
  inputs:
    command: "pytest"
    continue-on-error: true

# After
- id: test
  type: Shell
  inputs:
    command: "pytest"
  # metadata.succeeded = (exit_code == 0)

- id: notify_failure
  type: Shell
  inputs:
    command: "notify 'tests failed'"
  condition: ${blocks.test.failed}  # Clear!
```

### 5. Result.state Simplification

```python
class ResultState(str, Enum):
    SUCCESS = "success"          # Executor ran
    CRASHED = "error"    # Executor threw exception
    PAUSED = "paused"            # Executor paused for input

# FAILED removed - operation failures are metadata.failed=True
```

### 6. Executor Pattern

All executors signal operation success via `Result.metadata`:

```python
async def execute(self, inputs: BlockInput, context: dict[str, Any]) -> Result[BlockOutput]:
    try:
        # Run operation
        result = perform_operation()

        # Build output (DATA ONLY)
        output = SomeOutput(
            field1=value1,
            field2=value2
            # NO success field!
        )

        # Return SUCCESS with operation outcome in metadata
        return Result.success(
            output,
            metadata={
                "execution_time_ms": timer.elapsed_ms(),
                "operation_succeeded": result.succeeded,  # ← Signal outcome
                "error": result.error if result.failed else None
            }
        )
    except Exception as e:
        # CRASHED (executor failed to run)
        return Result.failure(f"Execution failed: {e}")
```

## Consequences

### Positive

✅ **Clear Separation**: Data vs state never mixed
✅ **Simple Conditions**: `${blocks.id.succeeded}` vs verbose exit_code checks
✅ **Error Access**: `${blocks.id.metadata.error}` always available
✅ **No Confusion**: `continue-on-error` removed
✅ **Standardized**: All blocks have same metadata structure
✅ **Pydantic Clean**: Output models contain only operation data

### Breaking Changes

❌ `continue-on-error` removed from Shell
❌ `success` field removed from outputs (CreateFile, ReadFile, etc.)
❌ `Result.FAILED` state removed
❌ All templates need updating

**Mitigation**: Breaking changes acceptable (one-off application, no migration needed)

## Implementation Plan

### Phase 1: Core Architecture (Critical Path)

1. **Update Result.state**
   - Remove `ResultState.FAILED`
   - Keep SUCCESS, CRASHED, PAUSED
   - Update all checks from `not result.is_success` to handle new semantics

2. **Update WorkflowExecutor**
   - Read `operation_succeeded` from Result.metadata
   - Populate `context["blocks"][id]["metadata"]` with:
     - `status` (detailed string)
     - `succeeded`, `failed`, `skipped` (boolean accessors)
     - `error` (error message if failed)

3. **Remove success from Output Models**
   - Remove `success` field from:
     - CreateFileOutput
     - ReadFileOutput
     - RenderTemplateOutput
     - ExecuteWorkflowOutput
     - WriteJSONStateOutput
     - MergeJSONStateOutput
   - Keep only data fields

### Phase 2: Executor Updates

4. **Shell Executor**
   - Remove `continue_on_error` from ShellInput
   - Always return `Result.success()`
   - Set `operation_succeeded = (exit_code == 0)` in metadata
   - Set `error = stderr` if exit_code != 0

5. **File Executors**
   - CreateFile: Set `operation_succeeded` based on file creation
   - ReadFile: Set `operation_succeeded` based on file read
   - RenderTemplate: Set `operation_succeeded` based on template rendering

6. **Workflow Composition**
   - ExecuteWorkflow: Set `operation_succeeded` based on child workflow status
   - Flatten child outputs as before (no change)

7. **Interactive Executor**
   - Prompt: Always set `operation_succeeded = True` (response received)

8. **State Executors**
   - ReadJSONState: Set based on read success
   - WriteJSONState: Set based on write success
   - MergeJSONState: Set based on merge success

### Phase 3: Variable Resolver

9. **Add Shortcut Accessors**
   - Support `${blocks.id.succeeded}` → checks metadata.succeeded
   - Support `${blocks.id.failed}` → checks metadata.failed
   - Support `${blocks.id.skipped}` → checks metadata.skipped
   - Fallback to explicit path if not found in metadata

10. **Update Tests**
    - Test shortcut syntax resolution
    - Test explicit metadata access
    - Test backward compatibility with outputs access

### Phase 4: Templates & Documentation

11. **Update All Templates**
    - Remove `continue-on-error` from Shell blocks
    - Change `${blocks.id.outputs.success}` → `${blocks.id.succeeded}`
    - Change `${blocks.id.outputs.exit_code} == 0` → `${blocks.id.succeeded}`
    - Add error handling with `${blocks.id.metadata.error}`

12. **Update Documentation**
    - CLAUDE.md: Document new patterns
    - README: Explain outputs vs metadata
    - Examples: Show condition patterns
    - Migration guide: Before/after examples

## Status Taxonomy

```python
class BlockStatus(str, Enum):
    """Detailed status for block execution."""

    SUCCESS = "success"  # Block ran, operation succeeded
    FAILED = "failure"  # Block ran, operation failed
    CRASHED = "crashed"    # Block couldn't run (exception)
    SKIPPED = "skipped"                    # Block didn't run (condition/dependency)
    PAUSED = "paused"                      # Block waiting for input
```

## Examples

### Shell Command with Failure Handling

```yaml
- id: test
  type: Shell
  inputs:
    command: "pytest"

- id: deploy
  type: Shell
  inputs:
    command: "./deploy.sh"
  condition: ${blocks.test.succeeded}
  depends_on:
    - block: test

- id: notify_failure
  type: Shell
  inputs:
    command: echo "Tests failed: ${blocks.test.metadata.error}"
  condition: ${blocks.test.failed}
  depends_on:
    - block: test
```

### File Operations

```yaml
- id: read_config
  type: ReadFile
  inputs:
    path: "config.json"
    required: false

- id: process_config
  type: Shell
  inputs:
    command: echo "Processing config..."
  condition: ${blocks.read_config.succeeded}

- id: use_defaults
  type: Shell
  inputs:
    command: echo "Using defaults"
  condition: ${blocks.read_config.failed}
```

### Workflow Composition

```yaml
- id: run_tests
  type: ExecuteWorkflow
  inputs:
    workflow: "python-ci-pipeline"

outputs:
  tests_passed: "${blocks.run_tests.succeeded}"
  test_error: "${blocks.run_tests.metadata.error}"
```

## Rollout

1. ✅ **Design approved** (this ADR)
2. **Implementation** (Phase 1-4 above)
3. **Testing** (comprehensive test updates)
4. **Documentation** (CLAUDE.md, examples)
5. **Templates** (update all built-in workflows)

## References

- [brainstorm-architecture-simplification.md](brainstorm-architecture-simplification.md) - Full analysis
- [investigation-result-structure.md](investigation-result-structure.md) - Current architecture
- GitHub Actions continue-on-error semantics (inspiration for original design)
