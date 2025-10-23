"""Comprehensive tests for AST-based condition evaluation.

Tests the security and functionality of the ConditionEvaluator with AST parsing.
"""

import pytest

from workflows_mcp.engine.variables import (
    ConditionEvaluator,
    InvalidConditionError,
)


class TestConditionEvaluatorAST:
    """Test suite for AST-based condition evaluation."""

    def setup_method(self):
        """Set up test fixtures."""
        self.evaluator = ConditionEvaluator()

    # =============================================================================
    # Basic Operator Tests
    # =============================================================================

    def test_comparison_operators(self):
        """Test all comparison operators work correctly."""
        context = {"a": 5, "b": 10, "c": 5}

        # Equality
        assert self.evaluator.evaluate("${a} == 5", context) is True
        assert self.evaluator.evaluate("${a} == ${c}", context) is True
        assert self.evaluator.evaluate("${a} == ${b}", context) is False

        # Inequality
        assert self.evaluator.evaluate("${a} != ${b}", context) is True
        assert self.evaluator.evaluate("${a} != ${c}", context) is False

        # Less than
        assert self.evaluator.evaluate("${a} < ${b}", context) is True
        assert self.evaluator.evaluate("${b} < ${a}", context) is False

        # Less than or equal
        assert self.evaluator.evaluate("${a} <= ${c}", context) is True
        assert self.evaluator.evaluate("${a} <= ${b}", context) is True

        # Greater than
        assert self.evaluator.evaluate("${b} > ${a}", context) is True
        assert self.evaluator.evaluate("${a} > ${b}", context) is False

        # Greater than or equal
        assert self.evaluator.evaluate("${b} >= ${a}", context) is True
        assert self.evaluator.evaluate("${a} >= ${c}", context) is True

    def test_boolean_operators(self):
        """Test boolean logic operators."""
        context = {"true_val": True, "false_val": False}

        # AND operator
        assert self.evaluator.evaluate("${true_val} and ${true_val}", context) is True
        assert self.evaluator.evaluate("${true_val} and ${false_val}", context) is False
        assert self.evaluator.evaluate("${false_val} and ${false_val}", context) is False

        # OR operator
        assert self.evaluator.evaluate("${true_val} or ${false_val}", context) is True
        assert self.evaluator.evaluate("${false_val} or ${false_val}", context) is False
        assert self.evaluator.evaluate("${true_val} or ${true_val}", context) is True

        # NOT operator
        assert self.evaluator.evaluate("not ${true_val}", context) is False
        assert self.evaluator.evaluate("not ${false_val}", context) is True

    def test_membership_operators(self):
        """Test 'in' and 'not in' operators."""
        context = {"value": "x", "list": ["x", "y", "z"], "empty": []}

        # IN operator
        assert self.evaluator.evaluate("${value} in ${list}", context) is True
        assert self.evaluator.evaluate("'a' in ${list}", context) is False
        assert self.evaluator.evaluate("'x' in ['x', 'y']", context) is True

        # NOT IN operator
        assert self.evaluator.evaluate("'a' not in ${list}", context) is True
        assert self.evaluator.evaluate("${value} not in ${list}", context) is False

    # =============================================================================
    # Complex Expression Tests
    # =============================================================================

    def test_complex_boolean_logic(self):
        """Test complex combinations of boolean operators."""
        context = {"a": 5, "b": 10, "c": 15, "d": True, "e": False}

        # Multiple AND
        assert self.evaluator.evaluate(
            "${a} < ${b} and ${b} < ${c} and ${d}", context
        ) is True

        # Multiple OR
        assert self.evaluator.evaluate(
            "${e} or ${a} > ${b} or ${b} < ${c}", context
        ) is True

        # Mixed AND/OR with precedence
        assert self.evaluator.evaluate(
            "${d} and (${e} or ${a} < ${b})", context
        ) is True
        assert self.evaluator.evaluate(
            "${d} or ${e} and ${a} > ${b}", context
        ) is True

        # Complex nested expressions
        assert self.evaluator.evaluate(
            "(${a} < ${b} and ${b} < ${c}) or (${d} and not ${e})", context
        ) is True

    def test_real_world_workflow_conditions(self):
        """Test conditions from real workflows."""
        context = {
            "inputs": {"run_tests_first": True, "environment": "dev", "build_artifacts": True},
            "blocks": {
                "run_tests": {"metadata": {"succeeded": True}},
                "build_artifacts": {"outputs": {"exit_code": 0}},
            },
        }

        # Simple boolean input
        assert self.evaluator.evaluate("${inputs.run_tests_first}", context) is True

        # Complex workflow condition from conditional-deploy.yaml
        condition = (
            "${inputs.build_artifacts} and "
            "(not ${inputs.run_tests_first} or ${blocks.run_tests.metadata.succeeded})"
        )
        assert self.evaluator.evaluate(condition, context) is True

        # Environment check with exit code
        condition = (
            "${inputs.environment} == 'dev' and "
            "(not ${inputs.build_artifacts} or ${blocks.build_artifacts.outputs.exit_code} == 0)"
        )
        assert self.evaluator.evaluate(condition, context) is True

    # =============================================================================
    # YAML Boolean Normalization Tests
    # =============================================================================

    def test_yaml_boolean_normalization(self):
        """Test YAML true/false conversion to Python True/False."""
        context = {}

        # Lowercase YAML booleans
        assert self.evaluator.evaluate("true", context) is True
        assert self.evaluator.evaluate("false", context) is False

        # In expressions
        assert self.evaluator.evaluate("true and false", context) is False
        assert self.evaluator.evaluate("true or false", context) is True
        assert self.evaluator.evaluate("not false", context) is True

    def test_string_boolean_normalization(self):
        """Test string boolean representations."""
        context = {"str_true": "True", "str_false": "False"}

        # String booleans should be normalized
        assert self.evaluator.evaluate("${str_true}", context) is True
        assert self.evaluator.evaluate("${str_false}", context) is False

    # =============================================================================
    # Literal Tests
    # =============================================================================

    def test_literal_values(self):
        """Test evaluation with literal values."""
        context = {}

        # Boolean literals
        assert self.evaluator.evaluate("True", context) is True
        assert self.evaluator.evaluate("False", context) is False

        # Number literals
        assert self.evaluator.evaluate("5 > 3", context) is True
        assert self.evaluator.evaluate("10.5 <= 20.0", context) is True

        # String literals
        assert self.evaluator.evaluate("'hello' == 'hello'", context) is True
        assert self.evaluator.evaluate('"test" != "other"', context) is True

        # List literals
        assert self.evaluator.evaluate("'x' in ['x', 'y', 'z']", context) is True

    # =============================================================================
    # Security Tests - Rejected Operations
    # =============================================================================

    def test_reject_function_calls(self):
        """Test that function calls are rejected."""
        context = {}

        with pytest.raises(InvalidConditionError, match="Unsupported expression type"):
            self.evaluator.evaluate("len([1, 2, 3]) > 0", context)

        with pytest.raises(InvalidConditionError, match="Unsupported expression type"):
            self.evaluator.evaluate("str(5) == '5'", context)

    def test_reject_attribute_access(self):
        """Test that attribute access is rejected."""
        context = {"obj": {"key": "value"}}

        with pytest.raises(InvalidConditionError, match="Unsupported expression type"):
            self.evaluator.evaluate("${obj}.key == 'value'", context)

    def test_reject_imports(self):
        """Test that import statements are rejected."""
        context = {}

        # Import statement should fail at parse stage
        with pytest.raises(InvalidConditionError, match="Invalid syntax"):
            self.evaluator.evaluate("import os; True", context)

    def test_reject_unsupported_operators(self):
        """Test that unsupported operators are rejected."""
        context = {"a": 5, "b": 2}

        # Power operator
        with pytest.raises(InvalidConditionError, match="Unsupported"):
            self.evaluator.evaluate("${a} ** ${b} > 10", context)

        # Bitwise operators
        with pytest.raises(InvalidConditionError, match="Unsupported"):
            self.evaluator.evaluate("${a} & ${b} == 0", context)

        with pytest.raises(InvalidConditionError, match="Unsupported"):
            self.evaluator.evaluate("${a} | ${b} > 0", context)

    def test_reject_list_comprehensions(self):
        """Test that comprehensions are rejected."""
        context = {}

        with pytest.raises(InvalidConditionError, match="Unsupported expression type"):
            self.evaluator.evaluate("[x for x in range(10)] != []", context)

    # =============================================================================
    # Error Handling Tests
    # =============================================================================

    def test_invalid_syntax(self):
        """Test handling of syntax errors."""
        context = {}

        with pytest.raises(InvalidConditionError, match="Invalid syntax"):
            self.evaluator.evaluate("True and and False", context)

        with pytest.raises(InvalidConditionError, match="Invalid syntax"):
            self.evaluator.evaluate("5 == ", context)

    def test_variable_not_found(self):
        """Test handling of missing variables."""
        context = {"existing": True}

        with pytest.raises(InvalidConditionError, match="Variable resolution failed"):
            self.evaluator.evaluate("${nonexistent} == True", context)

    def test_non_boolean_result(self):
        """Test that non-boolean results are rejected."""
        context = {"num": 42}

        with pytest.raises(InvalidConditionError, match="must evaluate to boolean"):
            self.evaluator.evaluate("${num}", context)

        # Binary operators like + are rejected as unsupported
        with pytest.raises(InvalidConditionError, match="Unsupported expression type"):
            self.evaluator.evaluate("5 + 3", context)

    # =============================================================================
    # Edge Cases
    # =============================================================================

    def test_empty_expression(self):
        """Test handling of empty expression."""
        context = {}

        with pytest.raises(InvalidConditionError):
            self.evaluator.evaluate("", context)

    def test_whitespace_handling(self):
        """Test that whitespace is handled correctly."""
        context = {"a": True, "b": False}

        # Extra whitespace should be fine
        assert self.evaluator.evaluate("  ${a}  and  ${b}  ", context) is False
        assert self.evaluator.evaluate("\n${a}\nor\n${b}\n", context) is True

    def test_parentheses_precedence(self):
        """Test that parentheses affect precedence correctly."""
        context = {}

        # Without parentheses: or has lower precedence
        assert self.evaluator.evaluate("False and True or True", context) is True

        # With parentheses: force different grouping
        assert self.evaluator.evaluate("False and (True or True)", context) is False

    def test_chained_comparisons(self):
        """Test chained comparison operations."""
        context = {"a": 5, "b": 10, "c": 15}

        # Python supports chained comparisons
        assert self.evaluator.evaluate("${a} < ${b} < ${c}", context) is True
        assert self.evaluator.evaluate("${a} < ${b} > 8", context) is True
        assert self.evaluator.evaluate("1 < 2 < 3 < 4", context) is True

    # =============================================================================
    # Performance Tests
    # =============================================================================

    def test_deeply_nested_expressions(self):
        """Test that deeply nested expressions work correctly."""
        context = {"t": True, "f": False}

        # 5 levels of nesting
        expr = "((((${t} and ${t}) or ${f}) and ${t}) or ${f}) and ${t}"
        assert self.evaluator.evaluate(expr, context) is True

    def test_many_operations(self):
        """Test expressions with many operations."""
        context = {"v": True}

        # 20 operations
        expr = " and ".join(["${v}"] * 20)
        assert self.evaluator.evaluate(expr, context) is True

        expr = " or ".join(["False"] * 19 + ["True"])
        assert self.evaluator.evaluate(expr, context) is True
