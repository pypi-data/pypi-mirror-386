# ADR-007: Industry-Aligned Block Status Reference Model

**Status**: Approved
**Date**: 2025-01-22
**Deciders**: Senior Python Developer, MCP Development Team
**Supersedes**: ADR-005 (extends shortcut accessor design)

## Context

ADR-005 introduced shortcut accessors for block state (`succeeded`, `failed`, `skipped`), but didn't standardize how template authors should reference block status across all use cases. Three distinct needs exist:

1. **Simple success checks** (90% of cases): "Did this step succeed?"
2. **Precise status checking**: "Did the executor run?" vs "Did the operation succeed?"
3. **String-based comparisons**: "Run cleanup if status is 'completed' OR 'skipped'"

Without standardization, templates use inconsistent patterns:
- `${blocks.id.succeeded}` (shortcut)
- `${blocks.id.metadata.succeeded}` (explicit)
- `${blocks.id.metadata.status}` (status enum)
- `${blocks.id.outputs.exit_code} == 0` (indirect)

## Industry Research

We analyzed status reference patterns from two leading workflow engines:

### GitHub Actions (Function-Based Shortcuts)

```yaml
# Tier 1: Simple functions
if: ${{ success() }}           # All previous steps succeeded
if: ${{ failure() }}           # Any previous step failed
if: ${{ always() }}            # Always runs

# Tier 2: Explicit field access
if: ${{ steps.demo.conclusion == 'failure' }}
if: ${{ steps.demo.outcome == 'success' }}
```

**Design Philosophy**: Simple shortcuts for common cases, explicit fields for precision.

### Argo Workflows (Template Variables)

```yaml
# Tier 1: Status checks
when: "{{workflow.status}} == Succeeded"    # Workflow-level
when: "{{status}} == Failed"                 # Step-level

# Tier 2: Depends logic (sophisticated)
depends: "task.Succeeded || task.Skipped"
depends: "(task-2.Succeeded || task-2.Skipped) && !task-3.Failed"

# Tier 3: Aggregates for loops
depends: "task-1.AnySucceeded || task-2.AllFailed"
```

**Design Philosophy**: Template variables with string comparisons, powerful dependency logic.

## Decision

Adopt a **three-tier progressive disclosure model** that combines the best of both approaches:

### Tier 1: Boolean Shortcuts (GitHub Actions Style)

**Syntax**: `${blocks.<id>.<check>}` → returns `"true"` or `"false"`

```yaml
# Simple property access (no function calls)
condition: "${blocks.run_tests.succeeded}"   # true if completed + success
condition: "${blocks.build.failed}"          # true if failed (any reason)
condition: "${blocks.lint.skipped}"          # true if skipped

# Workflow outputs
outputs:
  tests_passed: "${blocks.run_tests.succeeded}"
  deployment_failed: "${blocks.deploy.failed}"
```

**Semantics**:
- `succeeded` ≈ GitHub's `success()` - block completed successfully
- `failed` ≈ GitHub's `failure()` - block failed (executor crash OR operation failure)
- `skipped` ≈ Argo's `Skipped` - block didn't run (condition false or dependency not met)

### Tier 2: Status String (Argo Workflows Style)

**Syntax**: `${blocks.<id>.status}` → returns status string

```yaml
# String comparison for precision
condition: "${blocks.build.status} == 'completed'"   # Executor finished
condition: "${blocks.parse.status} == 'failed'"      # Executor crashed
condition: "${blocks.deploy.status} == 'paused'"     # Waiting for input

# Argo-style list checks
condition: >
  ${blocks.test.status} in ['completed', 'skipped'] &&
  ${blocks.build.status} != 'failed'
```

**Status Values**: `"pending"`, `"running"`, `"completed"`, `"failed"`, `"skipped"`, `"paused"`

**Use Case**: Determine if executor ran, regardless of operation success.

### Tier 3: Outcome String (Precision Enhancement)

**Syntax**: `${blocks.<id>.outcome}` → returns outcome string

```yaml
# Distinguish execution vs operation failure
condition: >
  ${blocks.build.status} == 'completed' &&
  ${blocks.build.outcome} == 'failure'    # Build ran but failed

# Cleanup regardless of success
condition: "${blocks.integration_test.status} == 'completed'"
```

**Outcome Values**: `"success"`, `"failure"`, `"n/a"`

**Use Case**: Separate "did executor run?" from "did operation succeed?"

## Implementation

### Variable Resolver Changes

```python
# Tier 1: Boolean shortcuts (transform to metadata access)
if segments == ["blocks", block_id, "succeeded"]:
    segments = ["blocks", block_id, "metadata", "succeeded"]

if segments == ["blocks", block_id, "failed"]:
    segments = ["blocks", block_id, "metadata", "failed"]

if segments == ["blocks", block_id, "skipped"]:
    segments = ["blocks", block_id, "metadata", "skipped"]

# Tier 2: Status string (transform to metadata.status)
if segments == ["blocks", block_id, "status"]:
    segments = ["blocks", block_id, "metadata", "status"]
    # Metadata.status is ExecutionStatus enum → converted to string value

# Tier 3: Outcome string (transform to metadata.outcome)
if segments == ["blocks", block_id, "outcome"]:
    segments = ["blocks", block_id, "metadata", "outcome"]
    # Metadata.outcome is OperationOutcome enum → converted to string value
```

### Enum to String Conversion

```python
def _format_for_string(self, value: Any) -> str:
    """Format value for regular string substitution."""
    from enum import Enum

    # Check Enum BEFORE str because ExecutionStatus/OperationOutcome inherit from str
    if isinstance(value, Enum):
        return value.value  # "completed", "success", etc.
    # ... rest of formatting logic
```

## Comparison with Industry Standards

| Aspect | GitHub Actions | Argo Workflows | Our Model |
|--------|----------------|----------------|-----------|
| **Shortcuts** | Functions: `success()` | Properties: `.Succeeded` | Properties: `.succeeded` |
| **Syntax** | `${{ }}` expressions | `{{ }}` templates | `${ }` variables |
| **Status Values** | `success`/`failure` | `Succeeded`/`Failed` | `success`/`failure` |
| **Precision** | `.conclusion`, `.outcome` | `.status` explicit | `.status`, `.outcome` |
| **Complexity** | Two-tier | Two-tier | Three-tier |

**Design Alignment**:
- ✅ Tier 1 matches GitHub Actions simplicity
- ✅ Tier 2 matches Argo Workflows power
- ✅ Tier 3 adds precision beyond both

## Examples

### Simple Success Check (Tier 1)

```yaml
blocks:
  - id: run_tests
    type: Shell
    inputs:
      command: pytest tests/

  - id: deploy
    type: Shell
    inputs:
      command: ./deploy.sh
    condition: "${blocks.run_tests.succeeded}"  # GitHub Actions style
    depends_on: [run_tests]
```

### Cleanup After Completion (Tier 2)

```yaml
blocks:
  - id: build_project
    type: Shell
    inputs:
      command: npm run build

  - id: cleanup
    type: Shell
    inputs:
      command: rm -rf node_modules/.cache
    # Run cleanup if build completed (success or failure)
    condition: "${blocks.build_project.status} == 'completed'"  # Argo style
    depends_on: [build_project]
```

### Distinguish Crash from Failure (Tier 3)

```yaml
blocks:
  - id: integration_test
    type: Shell
    inputs:
      command: npm run test:integration

  - id: notify_failure
    type: Shell
    inputs:
      command: |
        if [ "${blocks.integration_test.status}" = "failed" ]; then
          echo "Executor crashed - infrastructure issue"
        elif [ "${blocks.integration_test.outcome}" = "failure" ]; then
          echo "Tests failed - code issue"
        fi
    condition: "${blocks.integration_test.failed}"
    depends_on: [integration_test]
```

## Benefits

✅ **Familiar**: Developers recognize patterns from GitHub Actions and Argo
✅ **Progressive**: Simple for common cases, powerful for complex scenarios
✅ **Consistent**: One standardized pattern across all templates
✅ **Precise**: Clear separation between execution state and operation outcome
✅ **Backward Compatible**: Existing shortcuts (`metadata.succeeded`) still work
✅ **Industry-Aligned**: Follows established conventions from leading workflow engines

## Consequences

### Positive

1. **Reduced Cognitive Load**: Template authors use familiar patterns from GitHub/Argo
2. **Better Error Handling**: Can distinguish infrastructure failures from operation failures
3. **Cleaner Templates**: Shorter, more readable status checks
4. **Ecosystem Alignment**: Easier for users migrating from GitHub Actions or Argo
5. **Future Extensibility**: Room for aggregates like Argo's `.AnySucceeded`

### Neutral

1. **Three access patterns**: May require documentation examples for each tier
2. **Enum string conversion**: Additional complexity in variable resolver

### Negative

1. **Migration burden**: Minimal - all existing patterns remain valid
2. **Learning curve**: Users must understand when to use each tier

## Alternatives Considered

### Alternative 1: Keep ADR-005 Shortcuts Only

**Rejected**: Doesn't address string comparison use cases or precision needs.

### Alternative 2: Four-Tier Model (Original Proposal)

```yaml
Tier 1: ${blocks.id.succeeded}
Tier 2: ${blocks.id.status.completed}  # Property-style status checks
Tier 3: ${blocks.id.outcome.success}   # Property-style outcome checks
Tier 4: ${blocks.id.metadata.status}   # Raw enum access
```

**Rejected**: Too complex. String comparisons (`status == 'completed'`) are more familiar from industry standards than property accessors (`status.completed`).

### Alternative 3: GitHub Actions Functions

```yaml
condition: "${ success(blocks.build) }"
condition: "${ failure(blocks.test) }"
```

**Rejected**: Requires implementing a function call system in variable resolver. Properties are simpler and align with Argo Workflows style.

## Implementation Status

- ✅ Variable resolver updated with three-tier transformation logic
- ✅ Enum-to-string conversion implemented
- ✅ Comprehensive test suite (21 tests covering all tiers)
- ✅ Template comments updated to reference ADR-007
- ✅ Backward compatibility verified

## References

- ADR-005: Success State Architecture (shortcut accessors)
- ADR-006: Unified Execution Model (Metadata structure)
- GitHub Actions Documentation: [Conditional Execution](https://docs.github.com/en/actions/learn-github-actions/expressions)
- Argo Workflows Documentation: [Conditional Execution](https://github.com/argoproj/argo-workflows/blob/main/docs/walk-through/conditionals.md)
- Context7 Research: GitHub Actions & Argo Workflows patterns analysis
