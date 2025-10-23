"""Test ADR-007 three-tier industry-aligned block status reference model."""

from workflows_mcp.engine.metadata import Metadata
from workflows_mcp.engine.variables import ConditionEvaluator, VariableResolver


class TestTier1BooleanShortcuts:
    """Test Tier 1: Boolean shortcuts (GitHub Actions style)."""

    def test_succeeded_shortcut_true(self):
        """Test ${blocks.id.succeeded} returns True for successful execution."""
        metadata = Metadata.from_success(
            execution_time_ms=100.0,
            started_at="2025-01-22T10:00:00Z",
            completed_at="2025-01-22T10:00:01Z",
        )

        context = {
            "blocks": {
                "build": {
                    "outputs": {},
                    "metadata": metadata.model_dump(),
                }
            }
        }

        resolver = VariableResolver(context)
        result = resolver.resolve("${blocks.build.succeeded}")
        assert result == "true"  # Boolean formatted as lowercase string

    def test_succeeded_shortcut_false_when_failed(self):
        """Test ${blocks.id.succeeded} returns False when operation failed."""
        metadata = Metadata.from_operation_failure(
            message="Build failed",
            execution_time_ms=50.0,
            started_at="2025-01-22T10:00:00Z",
            completed_at="2025-01-22T10:00:01Z",
        )

        context = {
            "blocks": {
                "build": {
                    "outputs": {},
                    "metadata": metadata.model_dump(),
                }
            }
        }

        resolver = VariableResolver(context)
        result = resolver.resolve("${blocks.build.succeeded}")
        assert result == "false"

    def test_failed_shortcut_true_for_operation_failure(self):
        """Test ${blocks.id.failed} returns True for operation failure."""
        metadata = Metadata.from_operation_failure(
            message="Tests failed",
            execution_time_ms=200.0,
            started_at="2025-01-22T10:00:00Z",
            completed_at="2025-01-22T10:00:02Z",
        )

        context = {
            "blocks": {
                "test": {
                    "outputs": {},
                    "metadata": metadata.model_dump(),
                }
            }
        }

        resolver = VariableResolver(context)
        result = resolver.resolve("${blocks.test.failed}")
        assert result == "true"

    def test_failed_shortcut_true_for_execution_failure(self):
        """Test ${blocks.id.failed} returns True for executor crash."""
        metadata = Metadata.from_execution_failure(
            message="Executor crashed",
            execution_time_ms=10.0,
            started_at="2025-01-22T10:00:00Z",
            completed_at="2025-01-22T10:00:01Z",
        )

        context = {
            "blocks": {
                "deploy": {
                    "outputs": {},
                    "metadata": metadata.model_dump(),
                }
            }
        }

        resolver = VariableResolver(context)
        result = resolver.resolve("${blocks.deploy.failed}")
        assert result == "true"

    def test_skipped_shortcut_true(self):
        """Test ${blocks.id.skipped} returns True when block was skipped."""
        metadata = Metadata.from_skipped(
            message="Condition not met",
            timestamp="2025-01-22T10:00:00Z",
        )

        context = {
            "blocks": {
                "optional_step": {
                    "outputs": {},
                    "metadata": metadata.model_dump(),
                }
            }
        }

        resolver = VariableResolver(context)
        result = resolver.resolve("${blocks.optional_step.skipped}")
        assert result == "true"

    def test_shortcuts_in_conditions(self):
        """Test boolean shortcuts work correctly in conditional expressions."""
        # Successful build
        build_metadata = Metadata.from_success(
            execution_time_ms=100.0,
            started_at="2025-01-22T10:00:00Z",
            completed_at="2025-01-22T10:00:01Z",
        )

        # Failed test
        test_metadata = Metadata.from_operation_failure(
            message="Test failed",
            execution_time_ms=50.0,
            started_at="2025-01-22T10:00:00Z",
            completed_at="2025-01-22T10:00:01Z",
        )

        context = {
            "blocks": {
                "build": {"outputs": {}, "metadata": build_metadata.model_dump()},
                "test": {"outputs": {}, "metadata": test_metadata.model_dump()},
            }
        }

        evaluator = ConditionEvaluator()

        # Build succeeded
        assert evaluator.evaluate("${blocks.build.succeeded}", context) is True

        # Test failed
        assert evaluator.evaluate("${blocks.test.failed}", context) is True

        # Combined condition
        assert (
            evaluator.evaluate(
                "${blocks.build.succeeded} and ${blocks.test.failed}", context
            )
            is True
        )


class TestTier2StatusString:
    """Test Tier 2: Status string access (Argo Workflows style)."""

    def test_status_completed(self):
        """Test ${blocks.id.status} returns 'completed' for successful execution."""
        metadata = Metadata.from_success(
            execution_time_ms=100.0,
            started_at="2025-01-22T10:00:00Z",
            completed_at="2025-01-22T10:00:01Z",
        )

        context = {
            "blocks": {
                "build": {
                    "outputs": {},
                    "metadata": metadata.model_dump(),
                }
            }
        }

        resolver = VariableResolver(context)
        result = resolver.resolve("${blocks.build.status}")
        assert result == "completed"

    def test_status_failed(self):
        """Test ${blocks.id.status} returns 'failed' for executor crash."""
        metadata = Metadata.from_execution_failure(
            message="Crash",
            execution_time_ms=10.0,
            started_at="2025-01-22T10:00:00Z",
            completed_at="2025-01-22T10:00:01Z",
        )

        context = {
            "blocks": {
                "deploy": {
                    "outputs": {},
                    "metadata": metadata.model_dump(),
                }
            }
        }

        resolver = VariableResolver(context)
        result = resolver.resolve("${blocks.deploy.status}")
        assert result == "failed"

    def test_status_skipped(self):
        """Test ${blocks.id.status} returns 'skipped' for skipped blocks."""
        metadata = Metadata.from_skipped(
            message="Condition false",
            timestamp="2025-01-22T10:00:00Z",
        )

        context = {
            "blocks": {
                "optional": {
                    "outputs": {},
                    "metadata": metadata.model_dump(),
                }
            }
        }

        resolver = VariableResolver(context)
        result = resolver.resolve("${blocks.optional.status}")
        assert result == "skipped"

    def test_status_in_condition_string_comparison(self):
        """Test status strings work in conditional expressions with string comparison."""
        metadata = Metadata.from_success(
            execution_time_ms=100.0,
            started_at="2025-01-22T10:00:00Z",
            completed_at="2025-01-22T10:00:01Z",
        )

        context = {
            "blocks": {
                "build": {
                    "outputs": {},
                    "metadata": metadata.model_dump(),
                }
            }
        }

        evaluator = ConditionEvaluator()

        # String equality check
        assert (
            evaluator.evaluate("${blocks.build.status} == 'completed'", context) is True
        )

        # Inequality check
        assert evaluator.evaluate("${blocks.build.status} != 'failed'", context) is True

    def test_status_in_list_check(self):
        """Test status can be checked against list of values (Argo-style)."""
        completed_metadata = Metadata.from_success(
            execution_time_ms=100.0,
            started_at="2025-01-22T10:00:00Z",
            completed_at="2025-01-22T10:00:01Z",
        )

        skipped_metadata = Metadata.from_skipped(
            message="Skipped",
            timestamp="2025-01-22T10:00:00Z",
        )

        context_completed = {
            "blocks": {
                "step": {
                    "outputs": {},
                    "metadata": completed_metadata.model_dump(),
                }
            }
        }

        context_skipped = {
            "blocks": {
                "step": {
                    "outputs": {},
                    "metadata": skipped_metadata.model_dump(),
                }
            }
        }

        evaluator = ConditionEvaluator()

        # Check if status in list (cleanup if finished or skipped)
        condition = "${blocks.step.status} in ['completed', 'skipped']"
        assert evaluator.evaluate(condition, context_completed) is True
        assert evaluator.evaluate(condition, context_skipped) is True


class TestTier3OutcomeString:
    """Test Tier 3: Outcome string access (precision)."""

    def test_outcome_success(self):
        """Test ${blocks.id.outcome} returns 'success' for successful operation."""
        metadata = Metadata.from_success(
            execution_time_ms=100.0,
            started_at="2025-01-22T10:00:00Z",
            completed_at="2025-01-22T10:00:01Z",
        )

        context = {
            "blocks": {
                "build": {
                    "outputs": {},
                    "metadata": metadata.model_dump(),
                }
            }
        }

        resolver = VariableResolver(context)
        result = resolver.resolve("${blocks.build.outcome}")
        assert result == "success"

    def test_outcome_failure(self):
        """Test ${blocks.id.outcome} returns 'failure' for failed operation."""
        metadata = Metadata.from_operation_failure(
            message="Operation failed",
            execution_time_ms=50.0,
            started_at="2025-01-22T10:00:00Z",
            completed_at="2025-01-22T10:00:01Z",
        )

        context = {
            "blocks": {
                "test": {
                    "outputs": {},
                    "metadata": metadata.model_dump(),
                }
            }
        }

        resolver = VariableResolver(context)
        result = resolver.resolve("${blocks.test.outcome}")
        assert result == "failure"

    def test_outcome_not_applicable(self):
        """Test ${blocks.id.outcome} returns 'n/a' when not applicable."""
        metadata = Metadata.from_skipped(
            message="Skipped",
            timestamp="2025-01-22T10:00:00Z",
        )

        context = {
            "blocks": {
                "optional": {
                    "outputs": {},
                    "metadata": metadata.model_dump(),
                }
            }
        }

        resolver = VariableResolver(context)
        result = resolver.resolve("${blocks.optional.outcome}")
        assert result == "n/a"

    def test_outcome_in_condition(self):
        """Test outcome strings in conditional expressions."""
        metadata = Metadata.from_operation_failure(
            message="Build failed",
            execution_time_ms=100.0,
            started_at="2025-01-22T10:00:00Z",
            completed_at="2025-01-22T10:00:01Z",
        )

        context = {
            "blocks": {
                "build": {
                    "outputs": {},
                    "metadata": metadata.model_dump(),
                }
            }
        }

        evaluator = ConditionEvaluator()
        assert (
            evaluator.evaluate("${blocks.build.outcome} == 'failure'", context) is True
        )


class TestCombinedTierUsage:
    """Test combining multiple tiers in complex scenarios."""

    def test_status_and_outcome_precision(self):
        """Test distinguishing executor crash from operation failure."""
        # Operation failure (executor ran, operation failed)
        op_failure = Metadata.from_operation_failure(
            message="Tests failed",
            execution_time_ms=100.0,
            started_at="2025-01-22T10:00:00Z",
            completed_at="2025-01-22T10:00:01Z",
        )

        # Execution failure (executor crashed)
        exec_failure = Metadata.from_execution_failure(
            message="Executor crashed",
            execution_time_ms=10.0,
            started_at="2025-01-22T10:00:00Z",
            completed_at="2025-01-22T10:00:01Z",
        )

        context_op = {
            "blocks": {
                "test": {
                    "outputs": {},
                    "metadata": op_failure.model_dump(),
                }
            }
        }

        context_exec = {
            "blocks": {
                "test": {
                    "outputs": {},
                    "metadata": exec_failure.model_dump(),
                }
            }
        }

        evaluator = ConditionEvaluator()

        # Operation failure: status=completed, outcome=failure
        assert (
            evaluator.evaluate(
                "${blocks.test.status} == 'completed' and ${blocks.test.outcome} == 'failure'",
                context_op,
            )
            is True
        )

        # Execution failure: status=failed, outcome=n/a
        assert (
            evaluator.evaluate(
                "${blocks.test.status} == 'failed' and ${blocks.test.outcome} == 'n/a'",
                context_exec,
            )
            is True
        )

    def test_cleanup_after_completion_regardless_of_success(self):
        """Test running cleanup if build completed, regardless of success."""
        # Build completed but failed
        build_metadata = Metadata.from_operation_failure(
            message="Build failed",
            execution_time_ms=100.0,
            started_at="2025-01-22T10:00:00Z",
            completed_at="2025-01-22T10:00:01Z",
        )

        context = {
            "blocks": {
                "build": {
                    "outputs": {},
                    "metadata": build_metadata.model_dump(),
                }
            }
        }

        evaluator = ConditionEvaluator()

        # Cleanup should run if build completed (even if it failed)
        assert (
            evaluator.evaluate("${blocks.build.status} == 'completed'", context) is True
        )

        # But build did fail
        assert evaluator.evaluate("${blocks.build.failed}", context) is True

    def test_workflow_output_with_all_tiers(self):
        """Test workflow outputs using all three tiers."""
        metadata = Metadata.from_success(
            execution_time_ms=100.0,
            started_at="2025-01-22T10:00:00Z",
            completed_at="2025-01-22T10:00:01Z",
        )

        context = {
            "blocks": {
                "deploy": {
                    "outputs": {},
                    "metadata": metadata.model_dump(),
                }
            }
        }

        resolver = VariableResolver(context)

        # Tier 1: Simple success check
        assert resolver.resolve("${blocks.deploy.succeeded}") == "true"

        # Tier 2: Status string
        assert resolver.resolve("${blocks.deploy.status}") == "completed"

        # Tier 3: Outcome string
        assert resolver.resolve("${blocks.deploy.outcome}") == "success"

    def test_paused_status_handling(self):
        """Test status references work correctly for paused execution."""
        metadata = Metadata.from_paused(
            message="Waiting for input",
            execution_time_ms=50.0,
            started_at="2025-01-22T10:00:00Z",
            paused_at="2025-01-22T10:00:01Z",
        )

        context = {
            "blocks": {
                "approval": {
                    "outputs": {},
                    "metadata": metadata.model_dump(),
                }
            }
        }

        resolver = VariableResolver(context)

        # Tier 1: Not succeeded or failed
        assert resolver.resolve("${blocks.approval.succeeded}") == "false"
        assert resolver.resolve("${blocks.approval.failed}") == "false"
        assert resolver.resolve("${blocks.approval.skipped}") == "false"

        # Tier 2: Status is 'paused'
        assert resolver.resolve("${blocks.approval.status}") == "paused"

        # Tier 3: Outcome is n/a
        assert resolver.resolve("${blocks.approval.outcome}") == "n/a"


class TestBackwardCompatibility:
    """Test backward compatibility with existing ADR-005 patterns."""

    def test_metadata_shortcut_still_works(self):
        """Test that ${blocks.id.metadata.succeeded} still works."""
        metadata = Metadata.from_success(
            execution_time_ms=100.0,
            started_at="2025-01-22T10:00:00Z",
            completed_at="2025-01-22T10:00:01Z",
        )

        context = {
            "blocks": {
                "build": {
                    "outputs": {},
                    "metadata": metadata.model_dump(),
                }
            }
        }

        resolver = VariableResolver(context)

        # Old pattern still works
        result = resolver.resolve("${blocks.build.metadata.succeeded}")
        assert result == "true"

    def test_both_patterns_equivalent(self):
        """Test that shortcut and metadata access are equivalent."""
        metadata = Metadata.from_success(
            execution_time_ms=100.0,
            started_at="2025-01-22T10:00:00Z",
            completed_at="2025-01-22T10:00:01Z",
        )

        context = {
            "blocks": {
                "test": {
                    "outputs": {},
                    "metadata": metadata.model_dump(),
                }
            }
        }

        resolver = VariableResolver(context)

        # Both should return the same value
        shortcut = resolver.resolve("${blocks.test.succeeded}")
        explicit = resolver.resolve("${blocks.test.metadata.succeeded}")
        assert shortcut == explicit

        # Same for status and outcome
        status_shortcut = resolver.resolve("${blocks.test.status}")
        status_explicit = resolver.resolve("${blocks.test.metadata.status}")
        assert status_shortcut == status_explicit

        outcome_shortcut = resolver.resolve("${blocks.test.outcome}")
        outcome_explicit = resolver.resolve("${blocks.test.metadata.outcome}")
        assert outcome_shortcut == outcome_explicit
