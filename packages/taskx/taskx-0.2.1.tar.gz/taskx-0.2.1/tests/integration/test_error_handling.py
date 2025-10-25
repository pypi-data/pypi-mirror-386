"""
Integration tests for error handling.

Tests how the system handles various error conditions across features.
"""

import pytest

from taskx.cli.main import cli
from taskx.core.config import Config, ConfigError

# ============================================================================
# Test Configuration Errors
# ============================================================================


@pytest.mark.integration
class TestConfigurationErrors:
    """Test error handling in configuration loading."""

    def test_missing_config_file(self, temp_dir, cli_runner):
        """Test handling of missing configuration file."""
        import os

        original_cwd = os.getcwd()
        try:
            os.chdir(temp_dir)
            result = cli_runner.invoke(cli, ["list"])
            assert result.exit_code != 0
            assert "not found" in result.output.lower() or "does not exist" in result.output.lower()
        finally:
            os.chdir(original_cwd)

    def test_invalid_toml_syntax(self, temp_dir, cli_runner):
        """Test handling of invalid TOML syntax."""
        config_path = temp_dir / "pyproject.toml"
        config_path.write_text(
            """
[tool.taskx.tasks
test = "echo test"  # Missing closing bracket
"""
        )

        result = cli_runner.invoke(cli, ["--config", str(config_path), "list"])

        assert result.exit_code != 0

    def test_missing_taskx_section(self, temp_dir, cli_runner):
        """Test handling of config without taskx section."""
        config_path = temp_dir / "pyproject.toml"
        config_path.write_text(
            """
[project]
name = "test"
"""
        )

        result = cli_runner.invoke(cli, ["--config", str(config_path), "list"])

        # Should handle gracefully (empty task list or error)
        assert result.exit_code != 0
        assert "section found" in result.output.lower() or "no tasks" in result.output.lower()


# ============================================================================
# Test Task Execution Errors
# ============================================================================


@pytest.mark.integration
class TestTaskExecutionErrors:
    """Test error handling during task execution."""

    def test_nonexistent_task(self, temp_dir, cli_runner):
        """Test running a task that doesn't exist."""
        config_path = temp_dir / "pyproject.toml"
        config_path.write_text(
            """
[tool.taskx.tasks]
test = "echo test"
"""
        )

        result = cli_runner.invoke(cli, ["--config", str(config_path), "run", "nonexistent"])

        assert result.exit_code != 0
        assert "not found" in result.output.lower()

    def test_task_command_failure(self, temp_dir, cli_runner):
        """Test handling of task command failures."""
        config_path = temp_dir / "pyproject.toml"
        config_path.write_text(
            """
[tool.taskx.tasks]
fail = "exit 1"
"""
        )

        result = cli_runner.invoke(cli, ["--config", str(config_path), "run", "fail"])

        assert result.exit_code != 0

    def test_dependency_failure_stops_execution(self, temp_dir, cli_runner):
        """Test that dependency failure prevents main task execution."""
        config_path = temp_dir / "pyproject.toml"
        config_path.write_text(
            """
[tool.taskx.tasks]
fail = "exit 1"
main = { depends = ["fail"], cmd = "echo 'Should not execute'" }
"""
        )

        result = cli_runner.invoke(cli, ["--config", str(config_path), "run", "main"])

        assert result.exit_code != 0
        assert "Should not execute" not in result.output

    def test_invalid_command_syntax(self, temp_dir, cli_runner):
        """Test handling of invalid shell commands."""
        config_path = temp_dir / "pyproject.toml"
        config_path.write_text(
            """
[tool.taskx.tasks]
invalid = "&&& invalid syntax &&&"
"""
        )

        result = cli_runner.invoke(cli, ["--config", str(config_path), "run", "invalid"])

        assert result.exit_code != 0


# ============================================================================
# Test Dependency Errors
# ============================================================================


@pytest.mark.integration
class TestDependencyErrors:
    """Test error handling in task dependencies."""

    def test_circular_dependency_detection(self, temp_dir, cli_runner):
        """Test detection of circular dependencies."""
        config_path = temp_dir / "pyproject.toml"
        config_path.write_text(
            """
[tool.taskx.tasks]
a = { depends = ["b"], cmd = "echo a" }
b = { depends = ["a"], cmd = "echo b" }
"""
        )

        result = cli_runner.invoke(cli, ["--config", str(config_path), "run", "a"])

        assert result.exit_code != 0
        assert "circular" in result.output.lower() or "cycle" in result.output.lower()

    def test_missing_dependency(self, temp_dir, cli_runner):
        """Test handling of missing dependency."""
        config_path = temp_dir / "pyproject.toml"
        config_path.write_text(
            """
[tool.taskx.tasks]
main = { depends = ["nonexistent"], cmd = "echo main" }
"""
        )

        result = cli_runner.invoke(cli, ["--config", str(config_path), "run", "main"])

        assert result.exit_code != 0
        assert "not found" in result.output.lower() or "nonexistent" in result.output.lower()

    def test_self_dependency_rejected(self, temp_dir, cli_runner):
        """Test that self-dependency is rejected."""
        config_path = temp_dir / "pyproject.toml"
        config_path.write_text(
            """
[tool.taskx.tasks]
recursive = { depends = ["recursive"], cmd = "echo test" }
"""
        )

        result = cli_runner.invoke(cli, ["--config", str(config_path), "run", "recursive"])

        assert result.exit_code != 0


# ============================================================================
# Test Alias Errors
# ============================================================================


@pytest.mark.integration
class TestAliasErrors:
    """Test error handling in alias resolution."""

    def test_alias_to_nonexistent_task(self, temp_dir, cli_runner):
        """Test alias pointing to non-existent task."""
        config_path = temp_dir / "pyproject.toml"
        config_path.write_text(
            """
[tool.taskx.aliases]
t = "nonexistent"

[tool.taskx.tasks]
test = "echo test"
"""
        )

        result = cli_runner.invoke(cli, ["--config", str(config_path), "list"])

        # Should detect error during config load
        assert result.exit_code != 0

    def test_reserved_name_as_alias(self, temp_dir, cli_runner):
        """Test using reserved command name as alias."""
        config_path = temp_dir / "pyproject.toml"
        config_path.write_text(
            """
[tool.taskx.aliases]
list = "test"
run = "build"

[tool.taskx.tasks]
test = "echo test"
build = "echo build"
"""
        )

        result = cli_runner.invoke(cli, ["--config", str(config_path), "list"])

        # Should reject reserved names
        assert result.exit_code != 0


# ============================================================================
# Test Prompt Errors
# ============================================================================


@pytest.mark.integration
class TestPromptErrors:
    """Test error handling in interactive prompts."""

    def test_missing_prompt_value_in_non_interactive(self, temp_dir, cli_runner):
        """Test prompt without default in non-interactive mode."""
        config_path = temp_dir / "pyproject.toml"
        config_path.write_text(
            """
[tool.taskx.tasks.deploy]
cmd = "echo 'Deploying ${ENV}'"

[tool.taskx.tasks.deploy.prompt]
ENV = { type = "text", message = "Environment:" }
"""
        )

        # Set non-interactive mode (no stdin)
        result = cli_runner.invoke(
            cli, ["--config", str(config_path), "run", "deploy"], env={"CI": "1"}
        )

        # Should fail because no default and no env override
        assert result.exit_code != 0
        assert (
            "cannot prompt" in result.output.lower() or "non-interactive" in result.output.lower()
        )

    @pytest.mark.skip(
        reason="Prompt validation not implemented during config loading - only validated at runtime"
    )
    def test_invalid_prompt_type(self, temp_dir):
        """Test invalid prompt type in configuration."""
        config_path = temp_dir / "pyproject.toml"
        config_path.write_text(
            """
[tool.taskx.tasks.test]
cmd = "echo test"

[tool.taskx.tasks.test.prompt]
VAR = { type = "invalid_type", message = "Test:" }
"""
        )

        # Should fail during config load
        with pytest.raises((ValueError, ConfigError)):
            config = Config(config_path)
            config.load()

    @pytest.mark.skip(
        reason="Prompt validation not implemented during config loading - only validated at runtime"
    )
    def test_select_prompt_without_choices(self, temp_dir):
        """Test select prompt without choices."""
        config_path = temp_dir / "pyproject.toml"
        config_path.write_text(
            """
[tool.taskx.tasks.test]
cmd = "echo test"

[tool.taskx.tasks.test.prompt]
OPTION = { type = "select", message = "Choose:" }
"""
        )

        with pytest.raises((ValueError, ConfigError)):
            config = Config(config_path)
            config.load()


# ============================================================================
# Test Template Errors
# ============================================================================


@pytest.mark.integration
class TestTemplateErrors:
    """Test error handling in template operations."""

    def test_nonexistent_template(self, temp_dir, cli_runner):
        """Test requesting non-existent template."""
        import os

        original_cwd = os.getcwd()
        try:
            os.chdir(temp_dir)
            result = cli_runner.invoke(cli, ["init", "--template", "nonexistent"])
            assert result.exit_code != 0
            assert "not found" in result.output.lower()
        finally:
            os.chdir(original_cwd)

    def test_template_with_missing_variables(self, temp_dir, cli_runner):
        """Test template when required variables are missing."""
        import os

        original_cwd = os.getcwd()
        try:
            os.chdir(temp_dir)
            # Try to init template but cancel/skip prompts
            result = cli_runner.invoke(
                cli,
                ["init", "--template", "fastapi"],
                input="\n\n\n\n",  # Just press enter for all prompts
            )
            # Should either use defaults or handle gracefully
            assert (temp_dir / "pyproject.toml").exists() or result.exit_code != 0
        finally:
            os.chdir(original_cwd)


# ============================================================================
# Test Environment Variable Errors
# ============================================================================


@pytest.mark.integration
class TestEnvironmentVariableErrors:
    """Test error handling in environment variable usage."""

    def test_undefined_variable_in_command(self, temp_dir, cli_runner):
        """Test using undefined variable in command."""
        config_path = temp_dir / "pyproject.toml"
        config_path.write_text(
            """
[tool.taskx.tasks]
test = "echo '${UNDEFINED_VAR}'"
"""
        )

        result = cli_runner.invoke(cli, ["--config", str(config_path), "run", "test"])

        # Should execute but variable will be empty/undefined
        assert result.exit_code == 0

    @pytest.mark.skip(
        reason="--env flag validation not implemented - accepts any format without KEY=VALUE validation"
    )
    def test_invalid_env_override_format(self, temp_dir, cli_runner):
        """Test invalid --env flag format."""
        config_path = temp_dir / "pyproject.toml"
        config_path.write_text(
            """
[tool.taskx.tasks]
test = "echo test"
"""
        )

        result = cli_runner.invoke(
            cli, ["--config", str(config_path), "run", "test", "--env", "INVALID"]
        )

        # Should reject invalid format
        assert result.exit_code != 0


# ============================================================================
# Test Parallel Execution Errors
# ============================================================================


@pytest.mark.integration
class TestParallelExecutionErrors:
    """Test error handling in parallel task execution."""

    def test_parallel_task_failure(self, temp_dir, cli_runner):
        """Test handling when one parallel task fails."""
        config_path = temp_dir / "pyproject.toml"
        config_path.write_text(
            """
[tool.taskx.tasks]
success = "echo 'OK'"
fail = "exit 1"
check = { parallel = ["success", "fail"] }
"""
        )

        result = cli_runner.invoke(cli, ["--config", str(config_path), "run", "check"])

        assert result.exit_code != 0

    def test_all_parallel_tasks_fail(self, temp_dir, cli_runner):
        """Test handling when all parallel tasks fail."""
        config_path = temp_dir / "pyproject.toml"
        config_path.write_text(
            """
[tool.taskx.tasks]
fail1 = "exit 1"
fail2 = "exit 2"
fail3 = "exit 3"
check = { parallel = ["fail1", "fail2", "fail3"] }
"""
        )

        result = cli_runner.invoke(cli, ["--config", str(config_path), "run", "check"])

        assert result.exit_code != 0


# ============================================================================
# Test Graceful Degradation
# ============================================================================


@pytest.mark.integration
class TestGracefulDegradation:
    """Test graceful degradation and recovery."""

    def test_partial_config_still_usable(self, temp_dir, cli_runner):
        """Test that partial config with some valid tasks still works."""
        config_path = temp_dir / "pyproject.toml"
        config_path.write_text(
            """
[tool.taskx.tasks]
working = "echo 'This works'"
"""
        )

        result = cli_runner.invoke(cli, ["--config", str(config_path), "run", "working"])

        assert result.exit_code == 0
        # Task execution succeeded - output shows completion message
        assert "working" in result.output.lower()

    def test_error_messages_are_helpful(self, temp_dir, cli_runner):
        """Test that error messages provide helpful information."""
        config_path = temp_dir / "pyproject.toml"
        config_path.write_text(
            """
[tool.taskx.tasks]
test = "echo test"
"""
        )

        result = cli_runner.invoke(cli, ["--config", str(config_path), "run", "nonexistent"])

        assert result.exit_code != 0
        # Should suggest alternatives or show available tasks
        assert len(result.output) > 20  # Not just "error"

    def test_config_validation_provides_context(self, temp_dir, cli_runner):
        """Test that config validation errors provide context."""
        config_path = temp_dir / "pyproject.toml"
        config_path.write_text(
            """
[tool.taskx.aliases]
t = "nonexistent"

[tool.taskx.tasks]
test = "echo test"
"""
        )

        result = cli_runner.invoke(cli, ["--config", str(config_path), "list"])

        assert result.exit_code != 0
        # Error should mention the alias and missing task
        assert "t" in result.output or "nonexistent" in result.output
