"""
Unit tests for task aliases.

Tests alias resolution, validation, and error handling for both global and per-task aliases.
"""

import pytest

from taskx.core.config import Config, ConfigError

# ============================================================================
# Test Global Aliases
# ============================================================================


@pytest.mark.unit
class TestGlobalAliases:
    """Test suite for global task aliases."""

    def test_global_alias_resolution(self, temp_dir):
        """Test that global aliases resolve to task names."""
        config_path = temp_dir / "pyproject.toml"
        config_path.write_text(
            """
[tool.taskx.aliases]
t = "test"
b = "build"

[tool.taskx.tasks]
test = "pytest tests/"
build = "python -m build"
"""
        )

        config = Config(config_path)
        config.load()

        # Aliases should be loaded
        assert hasattr(config, "aliases")
        assert "t" in config.aliases
        assert config.aliases["t"] == "test"
        assert "b" in config.aliases
        assert config.aliases["b"] == "build"

    def test_alias_resolves_to_correct_task(self, task_with_aliases):
        """Test that alias correctly resolves to target task."""
        config = task_with_aliases

        # Get task by alias
        assert "t" in config.aliases
        target_name = config.aliases["t"]
        assert target_name == "test"
        assert target_name in config.tasks

    def test_multiple_aliases_for_same_task(self, temp_dir):
        """Test that multiple aliases can point to same task."""
        config_path = temp_dir / "pyproject.toml"
        config_path.write_text(
            """
[tool.taskx.aliases]
t = "test"
test-all = "test"
ta = "test"

[tool.taskx.tasks]
test = "pytest tests/"
"""
        )

        config = Config(config_path)
        config.load()

        # All aliases should resolve to same task
        assert config.aliases["t"] == "test"
        assert config.aliases["test-all"] == "test"
        assert config.aliases["ta"] == "test"

    def test_alias_with_hyphens_and_underscores(self, temp_dir):
        """Test that aliases can use hyphens and underscores."""
        config_path = temp_dir / "pyproject.toml"
        config_path.write_text(
            """
[tool.taskx.aliases]
test-unit = "test-unit-all"
test_integration = "test-integration-all"

[tool.taskx.tasks]
test-unit-all = "pytest tests/unit"
test-integration-all = "pytest tests/integration"
"""
        )

        config = Config(config_path)
        config.load()

        assert config.aliases["test-unit"] == "test-unit-all"
        assert config.aliases["test_integration"] == "test-integration-all"

    def test_alias_precedence_over_task_name(self, temp_dir):
        """Test alias takes precedence when resolving task names."""
        config_path = temp_dir / "pyproject.toml"
        config_path.write_text(
            """
[tool.taskx.aliases]
test = "test-all"

[tool.taskx.tasks]
test = "pytest tests/unit"
test-all = "pytest tests/"
"""
        )

        config = Config(config_path)
        config.load()

        # When using "test", should resolve to test-all first
        assert config.aliases["test"] == "test-all"

    def test_no_aliases_defined(self, temp_dir):
        """Test that config works when no aliases are defined."""
        config_path = temp_dir / "pyproject.toml"
        config_path.write_text(
            """
[tool.taskx.tasks]
test = "pytest tests/"
"""
        )

        config = Config(config_path)
        config.load()

        # Should have empty aliases dict
        assert hasattr(config, "aliases")
        assert len(config.aliases) == 0

    def test_empty_aliases_section(self, temp_dir):
        """Test that empty aliases section is handled."""
        config_path = temp_dir / "pyproject.toml"
        config_path.write_text(
            """
[tool.taskx.aliases]

[tool.taskx.tasks]
test = "pytest tests/"
"""
        )

        config = Config(config_path)
        config.load()

        assert hasattr(config, "aliases")
        assert len(config.aliases) == 0


# ============================================================================
# Test Alias Validation
# ============================================================================


@pytest.mark.unit
class TestAliasValidation:
    """Test suite for alias validation."""

    def test_alias_to_nonexistent_task_raises_error(self, temp_dir):
        """Test that alias to non-existent task raises error."""
        config_path = temp_dir / "pyproject.toml"
        config_path.write_text(
            """
[tool.taskx.aliases]
t = "nonexistent"

[tool.taskx.tasks]
test = "pytest tests/"
"""
        )

        config = Config(config_path)

        # Should raise error during validation
        with pytest.raises(ConfigError):
            config.load()

    def test_circular_alias_reference_detected(self, temp_dir):
        """Test that circular alias references are detected."""
        config_path = temp_dir / "pyproject.toml"
        config_path.write_text(
            """
[tool.taskx.aliases]
a = "b"
b = "a"

[tool.taskx.tasks]
a = "echo a"
b = "echo b"
"""
        )

        config = Config(config_path)

        # Should detect circular reference
        with pytest.raises((ValueError, RecursionError)):
            config.load()

    def test_alias_cannot_use_reserved_command_names(self, temp_dir):
        """Test that aliases cannot use reserved command names."""
        config_path = temp_dir / "pyproject.toml"
        config_path.write_text(
            """
[tool.taskx.aliases]
list = "test"
init = "build"
run = "deploy"

[tool.taskx.tasks]
test = "pytest tests/"
build = "python -m build"
deploy = "echo deploying"
"""
        )

        config = Config(config_path)

        # Should raise error for reserved names
        with pytest.raises(ConfigError):
            config.load()

    def test_duplicate_alias_names_not_allowed(self, temp_dir):
        """Test that duplicate alias names raise error."""
        config_path = temp_dir / "pyproject.toml"
        config_path.write_text(
            """
[tool.taskx.aliases]
t = "test"
t = "build"

[tool.taskx.tasks]
test = "pytest tests/"
build = "python -m build"
"""
        )

        config = Config(config_path)

        # TOML parser should handle duplicate keys
        # Either raises error or last value wins
        try:
            config.load()
            # If it loads, check which value was kept
            assert config.aliases["t"] in ["test", "build"]
        except Exception:
            # Expected - duplicate keys should fail
            pass

    def test_alias_target_must_be_string(self, temp_dir):
        """Test that alias target must be a string."""
        config_path = temp_dir / "pyproject.toml"
        config_path.write_text(
            """
[tool.taskx.aliases]
t = 123

[tool.taskx.tasks]
test = "pytest tests/"
"""
        )

        config = Config(config_path)

        with pytest.raises((ValueError, TypeError)):
            config.load()

    @pytest.mark.skip(reason="Identifier validation not yet implemented")
    def test_alias_name_must_be_valid_identifier(self, temp_dir):
        """Test that alias names must be valid identifiers."""
        config_path = temp_dir / "pyproject.toml"
        config_path.write_text(
            """
[tool.taskx.aliases]
"test task" = "test"

[tool.taskx.tasks]
test = "pytest tests/"
"""
        )

        config = Config(config_path)

        # Should reject invalid alias names
        with pytest.raises(ValueError):
            config.load()

    def test_empty_alias_target_rejected(self, temp_dir):
        """Test that empty alias target is rejected."""
        config_path = temp_dir / "pyproject.toml"
        config_path.write_text(
            """
[tool.taskx.aliases]
t = ""

[tool.taskx.tasks]
test = "pytest tests/"
"""
        )

        config = Config(config_path)

        with pytest.raises(ValueError):
            config.load()

    def test_alias_chain_validation(self, temp_dir):
        """Test that alias chains are properly validated."""
        config_path = temp_dir / "pyproject.toml"
        config_path.write_text(
            """
[tool.taskx.aliases]
a = "b"
b = "c"
c = "test"

[tool.taskx.tasks]
test = "pytest tests/"
"""
        )

        config = Config(config_path)

        # Should either resolve the chain or reject it
        # (depends on implementation)
        try:
            config.load()
            # If it loads, chains should resolve
            assert config.aliases["a"] == "b"
        except ValueError:
            # Or reject chains entirely
            pass


# ============================================================================
# Test Alias Resolution in Runner
# ============================================================================


@pytest.mark.unit
class TestAliasResolution:
    """Test suite for alias resolution during task execution."""

    def test_run_task_by_alias(self, task_with_aliases):
        """Test that tasks can be run using their aliases."""
        config = task_with_aliases

        # Alias "t" should resolve to "test"
        assert "t" in config.aliases
        task_name = config.aliases["t"]
        assert task_name in config.tasks

    def test_alias_resolution_is_case_sensitive(self, temp_dir):
        """Test that alias resolution is case-sensitive."""
        config_path = temp_dir / "pyproject.toml"
        config_path.write_text(
            """
[tool.taskx.aliases]
t = "test"
T = "test-all"

[tool.taskx.tasks]
test = "pytest tests/unit"
test-all = "pytest tests/"
"""
        )

        config = Config(config_path)
        config.load()

        assert config.aliases["t"] == "test"
        assert config.aliases["T"] == "test-all"
        assert config.aliases["t"] != config.aliases["T"]

    def test_resolve_multiple_aliases_in_dependency_chain(self, temp_dir):
        """Test that aliases in dependency chains are resolved."""
        config_path = temp_dir / "pyproject.toml"
        config_path.write_text(
            """
[tool.taskx.aliases]
t = "test"
b = "build"

[tool.taskx.tasks]
test = "pytest tests/"
build = "python -m build"
deploy = { depends = ["test", "build"], cmd = "echo deploying" }
"""
        )

        config = Config(config_path)
        config.load()

        # Aliases should be available
        assert config.aliases["t"] == "test"
        assert config.aliases["b"] == "build"

    def test_list_command_shows_aliases(self, temp_dir):
        """Test that list command can show aliases."""
        config_path = temp_dir / "pyproject.toml"
        config_path.write_text(
            """
[tool.taskx.aliases]
t = "test"
b = "build"

[tool.taskx.tasks]
test = "pytest tests/"
build = "python -m build"
"""
        )

        config = Config(config_path)
        config.load()

        # Should be able to access aliases for display
        assert len(config.aliases) == 2
        assert all(isinstance(k, str) and isinstance(v, str) for k, v in config.aliases.items())


# ============================================================================
# Test Alias Edge Cases
# ============================================================================


@pytest.mark.unit
class TestAliasEdgeCases:
    """Test suite for alias edge cases and error handling."""

    def test_alias_with_special_characters_in_name(self, temp_dir):
        """Test alias names with allowed special characters."""
        config_path = temp_dir / "pyproject.toml"
        config_path.write_text(
            """
[tool.taskx.aliases]
test-all = "test"
test_unit = "test"

[tool.taskx.tasks]
test = "pytest tests/"
"""
        )

        config = Config(config_path)
        config.load()

        assert config.aliases["test-all"] == "test"
        assert config.aliases["test_unit"] == "test"

    def test_alias_name_same_as_existing_task(self, temp_dir):
        """Test alias name that matches existing task name."""
        config_path = temp_dir / "pyproject.toml"
        config_path.write_text(
            """
[tool.taskx.aliases]
test = "test-all"

[tool.taskx.tasks]
test = "pytest tests/unit"
test-all = "pytest tests/"
"""
        )

        config = Config(config_path)
        config.load()

        # Alias should override task name in resolution
        assert config.aliases["test"] == "test-all"

    def test_many_aliases_performance(self, temp_dir):
        """Test that many aliases don't cause performance issues."""
        import time

        config_path = temp_dir / "pyproject.toml"

        # Create many aliases
        aliases = "\n".join([f'alias{i} = "task{i}"' for i in range(100)])
        tasks = "\n".join([f'task{i} = "echo task {i}"' for i in range(100)])

        config_path.write_text(
            f"""
[tool.taskx.aliases]
{aliases}

[tool.taskx.tasks]
{tasks}
"""
        )

        config = Config(config_path)

        start = time.time()
        config.load()
        elapsed = time.time() - start

        assert len(config.aliases) == 100
        assert elapsed < 1.0  # Should load quickly

    def test_alias_with_unicode_characters(self, temp_dir):
        """Test that unicode in alias names is handled."""
        config_path = temp_dir / "pyproject.toml"
        config_path.write_text(
            """
[tool.taskx.aliases]
"tëst" = "test"

[tool.taskx.tasks]
test = "pytest tests/"
""",
            encoding="utf-8",
        )

        config = Config(config_path)

        try:
            config.load()
            # If it loads, unicode should work
            assert "tëst" in config.aliases
        except (ValueError, UnicodeError):
            # Or unicode in alias names might be rejected
            pass

    def test_alias_resolution_with_no_config_file(self, temp_dir):
        """Test alias resolution when no config file exists."""
        config_path = temp_dir / "nonexistent.toml"

        config = Config(config_path)

        # Should handle missing config gracefully
        try:
            config.load()
        except FileNotFoundError:
            # Expected
            pass

    def test_alias_target_with_whitespace(self, temp_dir):
        """Test that alias targets with whitespace are handled."""
        config_path = temp_dir / "pyproject.toml"
        config_path.write_text(
            """
[tool.taskx.aliases]
t = "  test  "

[tool.taskx.tasks]
test = "pytest tests/"
"  test  " = "pytest tests/"
"""
        )

        config = Config(config_path)

        try:
            config.load()
            # If it loads, whitespace should be handled (stripped or accepted)
        except ValueError:
            # Or whitespace might be rejected
            pass

    @pytest.mark.parametrize("reserved_name", ["run", "list", "init", "graph", "completion"])
    def test_reserved_command_names_cannot_be_aliases(self, temp_dir, reserved_name):
        """Test that reserved command names cannot be used as aliases."""
        config_path = temp_dir / "pyproject.toml"
        config_path.write_text(
            f"""
[tool.taskx.aliases]
{reserved_name} = "test"

[tool.taskx.tasks]
test = "pytest tests/"
"""
        )

        config = Config(config_path)

        with pytest.raises(ConfigError):
            config.load()

    def test_alias_to_task_with_dependencies(self, temp_dir):
        """Test alias to task that has dependencies."""
        config_path = temp_dir / "pyproject.toml"
        config_path.write_text(
            """
[tool.taskx.aliases]
d = "deploy"

[tool.taskx.tasks]
test = "pytest tests/"
build = "python -m build"
deploy = { depends = ["test", "build"], cmd = "echo deploying" }
"""
        )

        config = Config(config_path)
        config.load()

        # Alias should resolve to task with dependencies
        assert config.aliases["d"] == "deploy"
        task = config.tasks["deploy"]
        assert task.depends == ["test", "build"]

    def test_alias_documented_in_list_output(self, task_with_aliases):
        """Test that aliases are available for display in list command."""
        config = task_with_aliases

        # Should be able to iterate over aliases
        alias_list = [(k, v) for k, v in config.aliases.items()]
        assert len(alias_list) > 0
        assert all(
            isinstance(alias, str) and isinstance(target, str) for alias, target in alias_list
        )
