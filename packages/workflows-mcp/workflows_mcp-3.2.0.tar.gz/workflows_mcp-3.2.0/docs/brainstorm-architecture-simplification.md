# Architecture Simplification & Improvement Brainstorm

**Date**: 2025-10-20
**Context**: Addressing confusion around block success/failure states and standardizing outputs

## Current Problems Analysis

### Problem 1: Three Overlapping "Success" Concepts

Currently, we have **three different ways** to represent success/failure:

```python
# 1. Result.state (Executor → Workflow Executor)
result.state: ResultState.SUCCESS | ResultState.FAILED | ResultState.PAUSED

# 2. metadata.status (Workflow Executor → Context)
context["blocks"]["id"]["metadata"]["status"]: "success" | "failure" | "skipped"

# 3. outputs.success (Some Executors → User Variables)
context["blocks"]["id"]["outputs"]["success"]: bool  # Only some executors!
```

**Confusion Examples:**

| Scenario | Result.state | metadata.status | outputs.success | What does it mean? |
|----------|--------------|-----------------|-----------------|-------------------|
| Shell exit_code=0 | SUCCESS | "success" | ❌ Not present | Command succeeded |
| Shell exit_code=1, continue_on_error=false | FAILED | "failure" | ❌ Not present | Command failed, block failed |
| Shell exit_code=1, continue_on_error=true | SUCCESS | "success" | ❌ Not present | Command failed, block "succeeded"? |
| CreateFile success | SUCCESS | "success" | ✅ true | File created |
| CreateFile failed | FAILED | "failure" | ❌ Not present (defaults) | File creation failed |
| ExecuteWorkflow child succeeded | SUCCESS | "success" | ✅ true | Child workflow succeeded |
| Condition=false (skipped) | - | "skipped" | ❌ false (default) | Block didn't run |

**Questions This Raises:**
1. Why does Shell with `continue_on_error=true` return `Result.SUCCESS` when the command failed?
2. How do users check if a Shell command actually succeeded vs just "didn't crash the workflow"?
3. Why do some executors have `success` in outputs and others don't?

---

### Problem 2: Execution State vs Logical Outcome Conflation

There's confusion between:
- **Execution State** (technical): Did the block execute?
- **Logical Outcome** (business): Was the operation successful?

**Example - Shell Executor:**
```bash
# Command: rm non-existent-file.txt
exit_code=1  # File doesn't exist
```

Two interpretations:
- **Execution succeeded**: The shell ran the command successfully (technical)
- **Operation failed**: The file wasn't deleted (business)

Current design conflates these:
```python
if not success:  # continue_on_error=false
    return Result.failure(...)  # Treats operation failure as execution failure
```

---

### Problem 3: Inconsistent Output Models

**Executors WITH `success` field:**
- CreateFile: `success: bool`
- ReadFile: `success: bool`
- RenderTemplate: `success: bool`
- ExecuteWorkflow: `success: bool`
- WriteJSONState: `success: bool`
- MergeJSONState: `success: bool`

**Executors WITHOUT `success` field:**
- Shell: Only has `exit_code`, `stdout`, `stderr`
- Prompt: Only has `response`
- ReadJSONState: Only has `data`, `found`

**Impact:**
```yaml
# This works
outputs:
  file_created: "${blocks.create_file.outputs.success}"

# This doesn't work
outputs:
  command_succeeded: "${blocks.run_command.outputs.success}"  # ❌ Field doesn't exist!

# User must do this instead
outputs:
  command_succeeded: "${blocks.run_command.outputs.exit_code} == 0"  # Verbose, error-prone
```

---

### Problem 4: Dependency Logic Partial Solution

Current `depends_on` with `required` helps but doesn't solve the core issue:

```yaml
blocks:
  - id: build
    type: Shell
    inputs:
      command: "make build"
    # If this fails (exit_code != 0), what happens?

  - id: test
    type: Shell
    inputs:
      command: "make test"
    depends_on:
      - block: build
        required: true  # test skips if build fails

  - id: notify
    type: Shell
    inputs:
      command: "slack-notify 'Build failed'"
    depends_on:
      - block: build
        required: false  # notify runs even if build fails
```

**This works but:**
- Still doesn't clarify what "build failed" means
- Users must understand `exit_code == 0` semantics
- No way to express "run if build succeeded" in a standard way

---

## Questions for Clarification

### Question 1: Execution State vs Logical Outcome

Should we separate these concepts?

**Option A: Keep conflated** (current approach)
- Simpler for simple cases
- Confusing for complex scenarios (continue-on-error)

**Option B: Separate execution from outcome**
```python
# Result.state = Did the executor run?
Result.state: SUCCESS | CRASHED | PAUSED

# BlockOutput.success = Was the operation successful?
output.success: bool  # Always present in all executors
```

**Example - Shell with separation:**
```python
# Command exits with code 1
return Result.success(  # Execution succeeded (command ran)
    ShellOutput(
        exit_code=1,
        success=False,  # Operation failed (command failed)
        stdout="...",
        stderr="..."
    )
)
```

Which approach do you prefer?

---

### Question 2: Standard Output Fields

Should ALL executors have these standard fields?

```python
class BlockOutput(BaseModel):
    # Standard fields (always present)
    success: bool  # Was the operation successful?
    message: str | None = None  # Optional human-readable message
    error: str | None = None  # Error message (if success=False)

    # Executor-specific fields via extra="allow"
    # Shell: exit_code, stdout, stderr
    # CreateFile: path, size_bytes, created
    # etc.

    model_config = {"extra": "allow"}
```

**Benefits:**
- Consistent interface for all blocks
- Users always use `${blocks.id.outputs.success}`
- Clear semantics: success=True means operation succeeded

**Tradeoffs:**
- Breaking change for existing workflows
- Some executors might find `success` ambiguous (Prompt: is success=True always?)

---

### Question 3: Status Taxonomy

Should we expand beyond success/failure/skipped?

**Current statuses:**
- `"success"` - Block ran, operation succeeded
- `"failure"` - Block ran, operation failed
- `"skipped"` - Block didn't run (condition false or dependency failed)

**Proposed expanded statuses:**
```python
class BlockStatus(str, Enum):
    # Execution states
    SUCCESS = "success"  # Ran, operation succeeded
    FAILED = "failure"  # Ran, operation failed
    CRASHED = "crashed"    # Couldn't run (exception, validation)
    SKIPPED = "skipped"                    # Didn't run (condition, dependency)
    PAUSED = "paused"                      # Waiting for input
```

**Use cases:**
```yaml
# Run cleanup whether build succeeded OR failed (but not if skipped)
- id: cleanup
  type: Shell
  inputs:
    command: "make clean"
  depends_on:
    - block: build
  condition: ${blocks.build.metadata.status} in ['success', 'failure']
```

Do we need this granularity?

---

### Question 4: Shell Executor `continue-on-error` Semantics

Current behavior is confusing:
```yaml
- id: test
  type: Shell
  inputs:
    command: "pytest"
    continue-on-error: true  # GitHub Actions semantics
```

**Current:**
- `continue-on-error=true` → Returns `Result.success()` even if exit_code != 0
- User must check `exit_code` manually to know if tests passed

**Should we change to:**
```yaml
- id: test
  type: Shell
  inputs:
    command: "pytest"
    continue-on-error: true
  # Always returns Result.success(output) where:
  # - output.success = (exit_code == 0)
  # - Result.state = SUCCESS (execution always succeeds)
```

Then users can:
```yaml
- id: deploy
  type: Shell
  condition: ${blocks.test.outputs.success}  # Check logical success
```

---

## Proposed Solutions

### Solution 1: Standardized Output Fields (Recommended)

**Add standard fields to ALL BlockOutput models:**

```python
class BlockOutput(BaseModel):
    """Base class for all block outputs with standard fields."""

    # Standard fields (always present in all executors)
    success: bool = Field(
        description="Whether the operation succeeded (business logic)"
    )
    error: str | None = Field(
        default=None,
        description="Error message if success=False"
    )

    # Executor-specific fields via extra="allow"
    model_config = {"extra": "allow"}
```

**Update all executors:**

```python
# Shell
class ShellOutput(BlockOutput):
    success: bool  # ← Already defined in base, override for clarity
    error: str | None = None  # ← Error message from stderr
    exit_code: int
    stdout: str
    stderr: str

    def __init__(self, **data):
        # Auto-populate success based on exit_code
        if 'success' not in data and 'exit_code' in data:
            data['success'] = (data['exit_code'] == 0)
        super().__init__(**data)

# CreateFile (already has success, no change needed)
class CreateFileOutput(BlockOutput):
    success: bool
    error: str | None = None
    path: str
    size_bytes: int
    created: bool

# Prompt (needs success added)
class PromptOutput(BlockOutput):
    success: bool = True  # Prompts always "succeed" if response received
    error: str | None = None
    response: str
```

**Benefits:**
- ✅ All blocks have consistent `${blocks.id.outputs.success}`
- ✅ Clear semantics: success=True means operation succeeded
- ✅ Error messages available via `${blocks.id.outputs.error}`
- ✅ Backward compatible (extra="allow" preserves existing fields)

**Migration Path:**
1. Add `success` field to BlockOutput base class
2. Update Shell, Prompt, ReadJSONState to include success
3. Document that `success` is semantic (operation outcome)
4. Deprecate direct `exit_code` checks in favor of `success`

---

### Solution 2: Separate Execution State from Logical Outcome

**Clarify Result.state semantics:**

```python
class ResultState(str, Enum):
    SUCCESS = "success"          # Executor ran successfully
    CRASHED = "error"    # Executor couldn't run (exception)
    PAUSED = "paused"            # Executor paused for input

# Remove FAILED from Result.state
# Failures are represented by Result.SUCCESS with output.success=False
```

**Update Shell executor:**

```python
async def execute(self, inputs: ShellInput, context: dict[str, Any]) -> Result[ShellOutput]:
    try:
        # Run command
        process = await asyncio.create_subprocess_shell(...)
        exit_code = process.returncode or 0

        # Build output with success field
        output = ShellOutput(
            exit_code=exit_code,
            stdout=stdout,
            stderr=stderr,
            success=(exit_code == 0),  # ← Logical outcome
            error=stderr if exit_code != 0 else None
        )

        # Always return Result.success() if command executed
        # (regardless of exit code)
        return Result.success(output, metadata={"execution_time_ms": timer.elapsed_ms()})

    except Exception as e:
        # Return CRASHED only for exceptions
        return Result.failure(f"Failed to execute command: {e}")
```

**Update workflow executor:**

```python
# Check Result.state for execution success
if result.state == ResultState.SUCCESS:
    # Check output.success for logical outcome
    logical_success = result.value.success

    context["blocks"][block_id]["metadata"] = {
        "status": "success" if logical_success else "failure",
        "execution_time_ms": execution_time,
    }
```

**Benefits:**
- ✅ Clear separation: Execution state (technical) vs Logical outcome (business)
- ✅ `continue-on-error` no longer needed (execution always succeeds)
- ✅ Users check `outputs.success` for operation result
- ✅ Dependent blocks can check either execution or logical success

**Tradeoffs:**
- 🔶 Breaking change (behavior change for failed commands)
- 🔶 All blocks must populate `success` field
- 🔶 Migration complexity

---

### Solution 3: Enhanced Dependency Logic

**Add `when` conditions to dependencies:**

```yaml
blocks:
  - id: build
    type: Shell
    inputs:
      command: "make build"

  - id: test
    type: Shell
    inputs:
      command: "make test"
    depends_on:
      - block: build
        when: success  # Only run if build.outputs.success=true

  - id: notify_failure
    type: Shell
    inputs:
      command: "slack-notify 'Build failed'"
    depends_on:
      - block: build
        when: failure  # Only run if build.outputs.success=false

  - id: cleanup
    type: Shell
    inputs:
      command: "make clean"
    depends_on:
      - block: build
        when: always  # Run regardless of build success/failure
```

**Implementation:**

```python
class DependencySpec(BaseModel):
    block: str
    required: bool = True
    when: Literal["success", "failure", "always"] = "success"

def _should_skip_due_to_dependencies(self, block_id, depends_on, context):
    for dep_spec in depends_on:
        dep_output = context["blocks"][dep_spec.block]["outputs"]
        dep_success = dep_output.get("success", True)

        # Check 'when' condition
        if dep_spec.when == "success" and not dep_success:
            if dep_spec.required:
                return (True, f"Dependency {dep_spec.block} failed")
        elif dep_spec.when == "failure" and dep_success:
            if dep_spec.required:
                return (True, f"Dependency {dep_spec.block} succeeded")
        # when="always" never skips

    return (False, None)
```

**Benefits:**
- ✅ Declarative dependency logic
- ✅ Clear intent (run on success/failure/always)
- ✅ Reduces need for complex conditions
- ✅ GitHub Actions-style familiar syntax

---

### Solution 4: Pydantic Class Hierarchy

**Create base class with standard fields:**

```python
# Base class with all standard fields
class StandardBlockOutput(BlockOutput):
    """Standard output fields for all executor types."""

    success: bool = Field(description="Operation succeeded")
    error: str | None = Field(default=None, description="Error message if failed")
    execution_time_ms: float | None = Field(default=None, description="Execution time")

    model_config = {"extra": "allow"}

# All executors inherit
class ShellOutput(StandardBlockOutput):
    exit_code: int
    stdout: str
    stderr: str

class CreateFileOutput(StandardBlockOutput):
    path: str
    size_bytes: int
    created: bool

class ExecuteWorkflowOutput(StandardBlockOutput):
    workflow: str
    total_blocks: int
    execution_waves: int
    # Child outputs flattened via extra="allow"
```

**Benefits:**
- ✅ DRY: Define standard fields once
- ✅ Type safety: All outputs guaranteed to have standard fields
- ✅ Easy to extend: Add new standard fields in base class
- ✅ IDE autocomplete works for standard fields

**Implementation:**

```python
# In executor_base.py
class StandardBlockOutput(BlockOutput):
    """Standard fields present in all block outputs."""

    success: bool = Field(
        description="Whether the operation completed successfully"
    )
    error: str | None = Field(
        default=None,
        description="Error message if success=False, None otherwise"
    )

    model_config = {"extra": "allow"}

# All executors update their output types
class ShellOutput(StandardBlockOutput):  # ← Change base class
    # Standard fields inherited: success, error
    exit_code: int
    stdout: str
    stderr: str
```

---

## Recommendations

### Phase 1: Quick Wins (Low Risk, High Value)

**1. Add `success` field to all outputs** (Solution 1)
- Update BlockOutput base class to include `success: bool`
- Update Shell, Prompt, ReadJSONState executors
- Document standard fields clearly
- **Impact**: Immediate consistency improvement
- **Risk**: Low (backward compatible via extra="allow")

**2. Create StandardBlockOutput base class** (Solution 4)
- Define standard fields once
- Migrate all executors to inherit
- **Impact**: Code simplification, DRY principle
- **Risk**: Low (Pydantic inheritance well-supported)

**3. Document success semantics clearly**
- Create guide: "When is a block successful?"
- Explain execution state vs logical outcome
- **Impact**: Reduced confusion
- **Risk**: None (documentation only)

### Phase 2: Architectural Changes (Higher Risk, Higher Value)

**4. Separate execution from outcome** (Solution 2)
- Remove Result.FAILED state
- Execution failures return Result.success(output) with output.success=False
- Reserve Result.failure() for exceptions only
- **Impact**: Clear separation of concerns
- **Risk**: Medium (breaking change, requires migration)

**5. Enhanced dependency logic** (Solution 3)
- Add `when: success|failure|always` to DependencySpec
- Update dependency checking logic
- **Impact**: Clearer workflow intent
- **Risk**: Low (additive change)

### Phase 3: Ecosystem Maturity

**6. Expand status taxonomy** (Solution 3)
- Add success, failure, crashed
- Update context metadata
- **Impact**: More precise status tracking
- **Risk**: Medium (behavior change)

---

## Open Questions for Discussion

1. **Should we do Phase 1 immediately?**
   - It's backward compatible and fixes the immediate pain point
   - Requires updating 3 executors (Shell, Prompt, ReadJSONState)

2. **Do you want execution state separate from logical outcome?**
   - Pro: Clear semantics, no confusion
   - Con: Breaking change, migration required

3. **Should `continue-on-error` be deprecated?**
   - If we separate execution from outcome, it's redundant
   - Commands can fail logically but execution always succeeds

4. **What should Prompt.success mean?**
   - Always True (response received)?
   - Based on response content?
   - Should prompts even have success semantics?

5. **Should we version this change?**
   - v4.0.0 with breaking changes?
   - Gradual migration with deprecation warnings?

---

## Answers & Decisions

### Q1: Most Painful Problem
**Answer**: `continue-on-error` makes `.success` state inconsistent. Need to check `exit_code` which isn't standardized.

**Impact**: This confusion propagates through entire workflow design.

### Q2: Breaking Changes
**Answer**: Breaking changes are acceptable! This is a one-off application, no migration effort needed.

**Impact**: We can design the ideal architecture without backward compatibility constraints.

### Q3: Where Should Success State Live?
**Answer**: NOT in outputs namespace! Prefer:
- Direct block accessor: `${blocks.run.succeeded}`
- Or in metadata: `${blocks.run.metadata.success}`

**Reasoning**: Outputs are for **operation data**, not **execution state**.

### Q4: Additional Requirements
- Need condition syntax for various block states
- Prefer Pydantic class hierarchy for logical simplicity
- Want clear separation between data and state

---

## Refined Architecture (Based on Answers)

### Core Principle: Separation of Concerns

```python
context["blocks"]["id"] = {
    "inputs": {...},           # What block received
    "outputs": {               # What block produced (DATA ONLY)
        "exit_code": 0,
        "stdout": "...",
        "stderr": "...",
        # NO success field here!
    },
    "metadata": {              # How block executed (STATE ONLY)
        "status": "success",
        "succeeded": True,     # ← Boolean accessor
        "failed": False,       # ← Boolean accessor
        "skipped": False,      # ← Boolean accessor
        "error": None,         # ← Error message if failed
        "execution_time_ms": 123.4
    }
}
```

### Key Changes

#### 1. Remove `success` from Outputs
```python
# OLD (confusing - state in data namespace)
class ShellOutput(BlockOutput):
    exit_code: int
    stdout: str
    stderr: str
    success: bool  # ❌ Remove this

# NEW (clean - only data)
class ShellOutput(BlockOutput):
    exit_code: int
    stdout: str
    stderr: str
    # No success field!
```

#### 2. Add Boolean Accessors to Metadata
```python
context["blocks"]["run"]["metadata"] = {
    "status": "success",  # Detailed status string
    "succeeded": True,             # Boolean: operation succeeded
    "failed": False,               # Boolean: operation failed
    "skipped": False,              # Boolean: didn't run
    "error": None,                 # Error message (if failed)
    "execution_time_ms": 123.4
}
```

#### 3. Variable Syntax for Conditions
```yaml
# Clear and explicit
condition: ${blocks.run.metadata.succeeded}
condition: ${blocks.run.metadata.failed}
condition: ${blocks.run.metadata.skipped}

# Or with shortcut (variable resolver checks metadata first)
condition: ${blocks.run.succeeded}  # ← Cleaner!
```

#### 4. Remove `continue-on-error` (Redundant)
```yaml
# OLD (confusing)
- id: test
  type: Shell
  inputs:
    command: "pytest"
    continue-on-error: true  # ❌ What does this mean?

# NEW (clear)
- id: test
  type: Shell
  inputs:
    command: "pytest"
  # Execution always succeeds
  # metadata.succeeded reflects exit_code == 0

- id: notify_failure
  type: Shell
  inputs:
    command: "slack-notify 'Tests failed'"
  condition: ${blocks.test.failed}  # ← Clear intent!
```

#### 5. Status Taxonomy
```python
class BlockStatus(str, Enum):
    SUCCESS = "success"  # Ran, operation succeeded
    FAILED = "failure"  # Ran, operation failed
    CRASHED = "crashed"    # Couldn't run (exception)
    SKIPPED = "skipped"                    # Didn't run (condition/dependency)
    PAUSED = "paused"                      # Waiting for input (interactive)
```

---

## Concrete Implementation Plan

### Phase 1: Result State Cleanup

**1. Simplify Result.state**
```python
class ResultState(str, Enum):
    SUCCESS = "success"          # Executor ran
    CRASHED = "error"    # Executor threw exception
    PAUSED = "paused"            # Executor paused

# Remove FAILED - operation failures are metadata.failed=True
```

**2. Update Executor Pattern**
```python
# Shell executor
async def execute(self, inputs: ShellInput, context: dict[str, Any]) -> Result[ShellOutput]:
    try:
        # Run command
        exit_code = process.returncode or 0

        # Build output (DATA ONLY - no success field)
        output = ShellOutput(
            exit_code=exit_code,
            stdout=stdout,
            stderr=stderr
        )

        # Return SUCCESS (execution succeeded)
        # Operation success determined by exit_code
        return Result.success(
            output,
            metadata={
                "execution_time_ms": timer.elapsed_ms(),
                "operation_succeeded": (exit_code == 0),  # ← Executor signals outcome
                "error": stderr if exit_code != 0 else None
            }
        )

    except Exception as e:
        # CRASHED (executor failed to run)
        return Result.failure(f"Failed to execute: {e}")
```

### Phase 2: Metadata Enhancement

**3. Enhance Metadata Storage**
```python
# In WorkflowExecutor._execute_wave()
if result.is_success:
    # Get operation success from executor metadata
    operation_succeeded = result.metadata.get("operation_succeeded", True)
    error_msg = result.metadata.get("error", None)

    context["blocks"][block_id]["metadata"] = {
        "wave": wave_idx,
        "execution_order": len(completed_blocks),
        "execution_time_ms": execution_time,
        "started_at": start_time,
        "completed_at": end_time,

        # Status fields
        "status": "success" if operation_succeeded else "failure",
        "succeeded": operation_succeeded,  # Boolean accessor
        "failed": not operation_succeeded,  # Boolean accessor
        "skipped": False,                  # Boolean accessor
        "error": error_msg,                # Error message
    }
```

### Phase 3: Pydantic Output Cleanup

**4. Remove success from Output Models**
```python
# Base class - NO success field
class BlockOutput(BaseModel):
    """Base class for block outputs - DATA ONLY."""
    model_config = {"extra": "allow"}

# Shell - just command results
class ShellOutput(BlockOutput):
    exit_code: int
    stdout: str
    stderr: str

# CreateFile - just file info
class CreateFileOutput(BlockOutput):
    path: str
    size_bytes: int
    created: bool

# ExecuteWorkflow - workflow info + child outputs
class ExecuteWorkflowOutput(BlockOutput):
    workflow: str
    execution_time_ms: float
    total_blocks: int
    execution_waves: int
    # Child outputs flattened via extra="allow"
```

### Phase 4: Variable Resolver Enhancement

**5. Add Block Property Accessors**
```python
# In VariableResolver
def resolve(self, value: Any) -> Any:
    """Resolve variables with shortcut accessors."""

    # Pattern: ${blocks.id.succeeded}
    # Check metadata first for convenience
    if pattern.match("${blocks.(?P<id>\\w+).(?P<accessor>succeeded|failed|skipped)}"):
        return context["blocks"][id]["metadata"][accessor]

    # Pattern: ${blocks.id.metadata.succeeded}
    # Explicit metadata access
    if pattern.match("${blocks.(?P<id>\\w+).metadata.(?P<field>\\w+)}"):
        return context["blocks"][id]["metadata"][field]

    # Pattern: ${blocks.id.outputs.field}
    # Explicit outputs access
    if pattern.match("${blocks.(?P<id>\\w+).outputs.(?P<field>\\w+)}"):
        return context["blocks"][id]["outputs"][field]
```

### Phase 5: Remove continue-on-error

**6. Deprecate continue-on-error**
```python
# Remove from ShellInput
class ShellInput(BlockInput):
    command: str
    working_dir: str = ""
    timeout: int = 120
    env: dict[str, str] = Field(default_factory=dict)
    capture_output: bool = True
    shell: bool = True
    # continue_on_error: bool = False  # ❌ REMOVED
```

**Migration**: All Shell blocks now always "succeed" at execution level. Check `metadata.succeeded` for operation outcome.

---

## Examples: Before vs After

### Example 1: Test and Deploy

**Before (Confusing):**
```yaml
- id: test
  type: Shell
  inputs:
    command: "pytest"
    continue-on-error: true  # What does this mean?

- id: deploy
  type: Shell
  inputs:
    command: "deploy.sh"
  condition: ${blocks.test.outputs.exit_code} == 0  # Verbose!
  depends_on:
    - block: test
      required: true
```

**After (Clear):**
```yaml
- id: test
  type: Shell
  inputs:
    command: "pytest"
  # Execution always succeeds
  # metadata.succeeded = (exit_code == 0)

- id: deploy
  type: Shell
  inputs:
    command: "deploy.sh"
  condition: ${blocks.test.succeeded}  # ✅ Simple and clear!
  depends_on:
    - block: test
      when: success  # Run only if test succeeded
```

### Example 2: Conditional Notifications

**Before (Complex):**
```yaml
- id: build
  type: Shell
  inputs:
    command: "make build"

- id: notify_success
  type: Shell
  inputs:
    command: "slack-notify 'Build succeeded'"
  condition: ${blocks.build.outputs.exit_code} == 0

- id: notify_failure
  type: Shell
  inputs:
    command: "slack-notify 'Build failed'"
  condition: ${blocks.build.outputs.exit_code} != 0
```

**After (Simple):**
```yaml
- id: build
  type: Shell
  inputs:
    command: "make build"

- id: notify_success
  type: Shell
  inputs:
    command: "slack-notify 'Build succeeded'"
  condition: ${blocks.build.succeeded}  # ✅ Clear!

- id: notify_failure
  type: Shell
  inputs:
    command: "slack-notify 'Build failed'"
  condition: ${blocks.build.failed}  # ✅ Clear!
```

### Example 3: Error Messages

**Before (No Access):**
```yaml
outputs:
  success: "${blocks.process.outputs.exit_code} == 0"
  # No way to get error message!
```

**After (Error Available):**
```yaml
outputs:
  success: "${blocks.process.succeeded}"
  error: "${blocks.process.metadata.error}"  # ✅ Error message accessible!
```

---

## Implementation Checklist

### Step 1: Core Architecture
- [ ] Remove `ResultState.FAILED`
- [ ] Add `operation_succeeded` to Result.metadata
- [ ] Update workflow executor to populate metadata.succeeded/failed/skipped
- [ ] Add BlockStatus enum

### Step 2: Output Models
- [ ] Remove `success` field from all BlockOutput subclasses
- [ ] Ensure outputs contain only data (no state)
- [ ] Document: "Outputs = operation data, Metadata = execution state"

### Step 3: Executor Updates
- [ ] Shell: Remove continue-on-error, always return Result.success()
- [ ] Shell: Set operation_succeeded based on exit_code
- [ ] CreateFile: Set operation_succeeded based on file creation
- [ ] ReadFile: Set operation_succeeded based on file read
- [ ] ExecuteWorkflow: Set operation_succeeded based on child workflow
- [ ] Prompt: Always set operation_succeeded=True
- [ ] All state executors: Set operation_succeeded appropriately

### Step 4: Variable Resolver
- [ ] Add shortcut accessors: ${blocks.id.succeeded}
- [ ] Support metadata access: ${blocks.id.metadata.error}
- [ ] Update tests for new syntax

### Step 5: Templates
- [ ] Update all workflow templates to use new syntax
- [ ] Remove continue-on-error from templates
- [ ] Use ${blocks.id.succeeded} instead of exit_code checks

### Step 6: Documentation
- [ ] Document new architecture clearly
- [ ] Explain outputs vs metadata separation
- [ ] Provide migration examples
- [ ] Update CLAUDE.md with new patterns

---

## Benefits Summary

✅ **Clear Separation**: Outputs=data, Metadata=state
✅ **Simple Conditions**: `${blocks.id.succeeded}` vs `${blocks.id.outputs.exit_code} == 0`
✅ **Error Access**: `${blocks.id.metadata.error}` available
✅ **Remove Confusion**: No more `continue-on-error` ambiguity
✅ **Pydantic Hierarchy**: Output models contain only data
✅ **Standardized**: All blocks have same metadata structure

This is the ideal architecture without backward compatibility constraints!
