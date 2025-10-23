"""Tests for ADR-005 shortcut accessors in VariableResolver."""

from workflows_mcp.engine.variables import VariableResolver


class TestShortcutAccessors:
    """Test shortcut accessors for block state (succeeded, failed, skipped)."""

    def test_succeeded_shortcut_resolves_to_metadata(self):
        """Test that ${blocks.id.succeeded} resolves to metadata.succeeded."""
        context = {
            "blocks": {
                "test_block": {
                    "metadata": {
                        "succeeded": True,
                        "failed": False,
                        "skipped": False,
                    }
                }
            }
        }

        resolver = VariableResolver(context)

        # Test shortcut syntax
        result = resolver.resolve("${blocks.test_block.succeeded}")
        assert result == "true"  # Lowercase per bash convention

        # Test that full syntax still works
        result_full = resolver.resolve("${blocks.test_block.metadata.succeeded}")
        assert result_full == "true"  # Lowercase per bash convention

    def test_failed_shortcut_resolves_to_metadata(self):
        """Test that ${blocks.id.failed} resolves to metadata.failed."""
        context = {
            "blocks": {
                "failing_block": {
                    "metadata": {
                        "succeeded": False,
                        "failed": True,
                        "skipped": False,
                    }
                }
            }
        }

        resolver = VariableResolver(context)

        # Test shortcut syntax
        result = resolver.resolve("${blocks.failing_block.failed}")
        assert result == "true"  # Lowercase per bash convention

        # Test that full syntax still works
        result_full = resolver.resolve("${blocks.failing_block.metadata.failed}")
        assert result_full == "true"  # Lowercase per bash convention

    def test_skipped_shortcut_resolves_to_metadata(self):
        """Test that ${blocks.id.skipped} resolves to metadata.skipped."""
        context = {
            "blocks": {
                "skipped_block": {
                    "metadata": {
                        "succeeded": False,
                        "failed": False,
                        "skipped": True,
                    }
                }
            }
        }

        resolver = VariableResolver(context)

        # Test shortcut syntax
        result = resolver.resolve("${blocks.skipped_block.skipped}")
        assert result == "true"  # Lowercase per bash convention

        # Test that full syntax still works
        result_full = resolver.resolve("${blocks.skipped_block.metadata.skipped}")
        assert result_full == "true"  # Lowercase per bash convention

    def test_shortcut_in_condition_context(self):
        """Test shortcuts work in condition evaluation context."""
        context = {
            "blocks": {
                "test_block": {
                    "metadata": {
                        "succeeded": True,
                        "failed": False,
                        "skipped": False,
                    },
                    "outputs": {"exit_code": 0},
                }
            }
        }

        resolver = VariableResolver(context)

        # Test shortcut in string interpolation
        result = resolver.resolve("Block succeeded: ${blocks.test_block.succeeded}")
        assert result == "Block succeeded: true"  # Lowercase per bash convention

        # Test shortcut for_eval (used in conditions)
        result_eval = resolver.resolve("${blocks.test_block.succeeded}", for_eval=True)
        assert result_eval == "True"  # for_eval returns Python bool repr for conditions

    def test_shortcut_does_not_apply_to_non_shortcut_fields(self):
        """Test that shortcuts only apply to succeeded/failed/skipped."""
        context = {
            "blocks": {
                "test_block": {
                    "outputs": {"result": "success"},
                    "metadata": {"execution_time_ms": 100},
                }
            }
        }

        resolver = VariableResolver(context)

        # Accessing outputs should work normally (no shortcut)
        result = resolver.resolve("${blocks.test_block.outputs.result}")
        assert result == "success"

        # Accessing metadata fields should work normally (no shortcut)
        result_meta = resolver.resolve("${blocks.test_block.metadata.execution_time_ms}")
        assert result_meta == "100"

    def test_shortcut_with_multiple_blocks(self):
        """Test shortcuts work correctly with multiple blocks."""
        context = {
            "blocks": {
                "block_a": {
                    "metadata": {
                        "succeeded": True,
                        "failed": False,
                        "skipped": False,
                    }
                },
                "block_b": {
                    "metadata": {
                        "succeeded": False,
                        "failed": True,
                        "skipped": False,
                    }
                },
                "block_c": {
                    "metadata": {
                        "succeeded": False,
                        "failed": False,
                        "skipped": True,
                    }
                },
            }
        }

        resolver = VariableResolver(context)

        # Test multiple shortcuts in one string
        result = resolver.resolve(
            "A: ${blocks.block_a.succeeded}, "
            "B: ${blocks.block_b.failed}, "
            "C: ${blocks.block_c.skipped}"
        )
        assert result == "A: true, B: true, C: true"  # Lowercase per bash convention

    def test_shortcut_with_dict_resolution(self):
        """Test shortcuts work in dict resolution."""
        context = {
            "blocks": {
                "test_block": {
                    "metadata": {
                        "succeeded": True,
                        "failed": False,
                        "skipped": False,
                    }
                }
            }
        }

        resolver = VariableResolver(context)

        # Test dict with shortcut references
        input_dict = {
            "success_status": "${blocks.test_block.succeeded}",
            "failure_status": "${blocks.test_block.failed}",
        }

        resolved = resolver.resolve(input_dict)
        assert resolved["success_status"] == "true"  # Lowercase per bash convention
        assert resolved["failure_status"] == "false"  # Lowercase per bash convention

    def test_shortcut_with_list_resolution(self):
        """Test shortcuts work in list resolution."""
        context = {
            "blocks": {
                "block_a": {"metadata": {"succeeded": True, "failed": False, "skipped": False}},
                "block_b": {"metadata": {"succeeded": False, "failed": True, "skipped": False}},
            }
        }

        resolver = VariableResolver(context)

        # Test list with shortcut references
        input_list = ["${blocks.block_a.succeeded}", "${blocks.block_b.failed}"]

        resolved = resolver.resolve(input_list)
        assert resolved == ["true", "true"]  # Lowercase per bash convention
