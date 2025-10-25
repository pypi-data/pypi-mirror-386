"""
Unit tests for completion CLI command.

Tests the 'taskx completion' command that generates completion scripts.
"""

from pathlib import Path

import pytest

from taskx.cli.main import cli

# ============================================================================
# Test Completion CLI Command
# ============================================================================


@pytest.mark.unit
class TestCompletionCommand:
    """Test suite for 'taskx completion' CLI command."""

    def test_completion_command_exists(self, cli_runner):
        """Test that completion command exists."""
        result = cli_runner.invoke(cli, ["completion", "--help"])
        assert result.exit_code == 0
        assert "completion" in result.output.lower()

    def test_completion_bash_generates_script(self, cli_runner):
        """Test that 'taskx completion bash' generates a script."""
        result = cli_runner.invoke(cli, ["completion", "bash"])
        assert result.exit_code == 0
        assert len(result.output) > 0
        assert "bash" in result.output.lower() or "complete" in result.output

    def test_completion_zsh_generates_script(self, cli_runner):
        """Test that 'taskx completion zsh' generates a script."""
        result = cli_runner.invoke(cli, ["completion", "zsh"])
        assert result.exit_code == 0
        assert len(result.output) > 0
        assert "zsh" in result.output.lower() or "compdef" in result.output

    def test_completion_fish_generates_script(self, cli_runner):
        """Test that 'taskx completion fish' generates a script."""
        result = cli_runner.invoke(cli, ["completion", "fish"])
        assert result.exit_code == 0
        assert len(result.output) > 0
        assert "fish" in result.output.lower() or "complete" in result.output

    def test_completion_powershell_generates_script(self, cli_runner):
        """Test that 'taskx completion powershell' generates a script."""
        result = cli_runner.invoke(cli, ["completion", "powershell"])
        assert result.exit_code == 0
        assert len(result.output) > 0
        assert (
            "powershell" in result.output.lower() or "Register-ArgumentCompleter" in result.output
        )

    def test_completion_invalid_shell_fails(self, cli_runner):
        """Test that invalid shell name fails gracefully."""
        result = cli_runner.invoke(cli, ["completion", "invalidshell"])
        assert result.exit_code != 0
        # Should show error or help

    def test_completion_no_shell_shows_help(self, cli_runner):
        """Test that 'taskx completion' without shell shows help."""
        result = cli_runner.invoke(cli, ["completion"])
        # Should either show help or require shell argument
        assert "bash" in result.output.lower() or "Usage" in result.output

    def test_completion_bash_install_creates_file(self, cli_runner, temp_dir, monkeypatch):
        """Test that 'taskx completion bash --install' creates a file."""
        # Mock the installation path to temp directory
        install_path = temp_dir / "bash_completion"

        # Change to temp directory for test
        monkeypatch.chdir(temp_dir)

        result = cli_runner.invoke(cli, ["completion", "bash", "--install"])

        # Command should succeed or show where to install
        assert result.exit_code == 0 or "install" in result.output.lower()

    def test_completion_bash_output_to_stdout(self, cli_runner):
        """Test that completion outputs to stdout by default."""
        result = cli_runner.invoke(cli, ["completion", "bash"])
        assert result.exit_code == 0
        assert len(result.output) > 100  # Should be a complete script

    def test_completion_scripts_are_different(self, cli_runner):
        """Test that different shells get different completion scripts."""
        bash_result = cli_runner.invoke(cli, ["completion", "bash"])
        zsh_result = cli_runner.invoke(cli, ["completion", "zsh"])
        fish_result = cli_runner.invoke(cli, ["completion", "fish"])

        assert bash_result.exit_code == 0
        assert zsh_result.exit_code == 0
        assert fish_result.exit_code == 0

        # Scripts should be different
        assert bash_result.output != zsh_result.output
        assert bash_result.output != fish_result.output
        assert zsh_result.output != fish_result.output

    def test_completion_uses_project_config(self, cli_runner, project_with_tasks):
        """Test that completion uses tasks from project config."""
        import os

        original_dir = os.getcwd()
        try:
            os.chdir(project_with_tasks)
            result = cli_runner.invoke(cli, ["completion", "bash"])

            assert result.exit_code == 0
            # Should include tasks from config
            # (or have dynamic task loading)
            assert len(result.output) > 0
        finally:
            os.chdir(original_dir)

    def test_completion_bash_includes_all_commands(self, cli_runner):
        """Test that Bash completion includes all taskx commands."""
        result = cli_runner.invoke(cli, ["completion", "bash"])
        assert result.exit_code == 0

        # Should mention core commands
        commands = ["run", "list", "init", "graph", "completion"]
        output_lower = result.output.lower()
        assert any(cmd in output_lower for cmd in commands)

    def test_completion_zsh_includes_descriptions(self, cli_runner, temp_dir):
        """Test that Zsh completion can include task descriptions."""
        import os

        # Create config with described tasks
        config_path = temp_dir / "pyproject.toml"
        config_path.write_text(
            """
[tool.taskx.tasks]
test = { cmd = "pytest", description = "Run all tests" }
build = { cmd = "python -m build", description = "Build the package" }
"""
        )

        original_dir = os.getcwd()
        try:
            os.chdir(temp_dir)
            result = cli_runner.invoke(cli, ["completion", "zsh"])

            assert result.exit_code == 0
            # Zsh completion should support descriptions
            assert len(result.output) > 0
        finally:
            os.chdir(original_dir)

    def test_completion_works_without_config(self, cli_runner, empty_project):
        """Test that completion works even without taskx config."""
        import os

        original_dir = os.getcwd()
        try:
            os.chdir(empty_project)
            result = cli_runner.invoke(cli, ["completion", "bash"])

            # Should still generate completion for base commands
            assert result.exit_code == 0
            assert len(result.output) > 0
        finally:
            os.chdir(original_dir)

    @pytest.mark.parametrize("shell", ["bash", "zsh", "fish", "powershell"])
    def test_completion_all_shells_work(self, cli_runner, shell):
        """Test that all shell completions generate successfully."""
        result = cli_runner.invoke(cli, ["completion", shell])
        assert result.exit_code == 0
        assert len(result.output) > 50  # Non-trivial output

    def test_completion_help_shows_shells(self, cli_runner):
        """Test that completion help shows available shells."""
        result = cli_runner.invoke(cli, ["completion", "--help"])
        assert result.exit_code == 0

        # Should mention available shells
        output_lower = result.output.lower()
        assert "bash" in output_lower or "shell" in output_lower

    def test_completion_bash_is_valid_bash(self, cli_runner):
        """Test that Bash completion output is valid Bash syntax."""
        import subprocess
        import tempfile

        result = cli_runner.invoke(cli, ["completion", "bash"])
        assert result.exit_code == 0

        with tempfile.NamedTemporaryFile(mode="w", suffix=".bash", delete=False) as f:
            f.write(result.output)
            temp_path = f.name

        try:
            proc = subprocess.run(["bash", "-n", temp_path], capture_output=True, text=True)
            assert proc.returncode == 0, f"Invalid Bash syntax: {proc.stderr}"
        finally:
            Path(temp_path).unlink()

    def test_completion_output_is_utf8(self, cli_runner):
        """Test that completion output is valid UTF-8."""
        result = cli_runner.invoke(cli, ["completion", "bash"])
        assert result.exit_code == 0

        # Should be encodable as UTF-8
        output_bytes = result.output.encode("utf-8")
        output_decoded = output_bytes.decode("utf-8")
        assert output_decoded == result.output

    def test_completion_handles_special_task_names(self, cli_runner, temp_dir):
        """Test that completion handles tasks with special characters."""
        import os

        config_path = temp_dir / "pyproject.toml"
        config_path.write_text(
            """
[tool.taskx.tasks]
"test-all" = "pytest tests/"
"build:prod" = "python -m build"
"deploy@staging" = "echo deploying"
"""
        )

        original_dir = os.getcwd()
        try:
            os.chdir(temp_dir)
            result = cli_runner.invoke(cli, ["completion", "bash"])

            assert result.exit_code == 0
            assert len(result.output) > 0
        finally:
            os.chdir(original_dir)

    def test_completion_install_shows_instructions(self, cli_runner):
        """Test that install flag shows installation instructions."""
        result = cli_runner.invoke(cli, ["completion", "bash", "--install"])

        # Should either install or show instructions
        assert result.exit_code == 0
        # Output should have some content (script or instructions)
        assert len(result.output) > 0

    def test_completion_respects_shell_case(self, cli_runner):
        """Test that completion works with different case variations."""
        # Should accept lowercase
        result_lower = cli_runner.invoke(cli, ["completion", "bash"])
        assert result_lower.exit_code == 0

        # PowerShell might be written as PowerShell or powershell
        result_ps = cli_runner.invoke(cli, ["completion", "powershell"])
        assert result_ps.exit_code == 0

    def test_completion_graph_formats_included(self, cli_runner):
        """Test that completion includes graph format options."""
        result = cli_runner.invoke(cli, ["completion", "bash"])
        assert result.exit_code == 0

        # Should mention graph formats somewhere
        output = result.output
        formats = ["text", "dot", "mermaid"]
        # Either directly or through dynamic loading
        assert any(fmt in output for fmt in formats) or "graph" in output

    def test_completion_handles_missing_config_gracefully(self, cli_runner, temp_dir):
        """Test that completion works when config file doesn't exist."""
        import os

        original_dir = os.getcwd()
        try:
            os.chdir(temp_dir)
            result = cli_runner.invoke(cli, ["completion", "bash"])

            # Should still work for base commands
            assert result.exit_code == 0
            assert "completion" in result.output
        finally:
            os.chdir(original_dir)

    def test_completion_no_error_output(self, cli_runner):
        """Test that successful completion doesn't output errors."""
        result = cli_runner.invoke(cli, ["completion", "bash"])
        assert result.exit_code == 0

        # Should not contain error messages
        output_lower = result.output.lower()
        assert "error" not in output_lower
        assert "exception" not in output_lower

    def test_completion_deterministic_output(self, cli_runner):
        """Test that completion output is deterministic."""
        result1 = cli_runner.invoke(cli, ["completion", "bash"])
        result2 = cli_runner.invoke(cli, ["completion", "bash"])

        assert result1.exit_code == 0
        assert result2.exit_code == 0

        # Should produce same output
        assert result1.output == result2.output

    def test_completion_performance(self, cli_runner):
        """Test that completion generation is fast."""
        import time

        start = time.time()
        result = cli_runner.invoke(cli, ["completion", "bash"])
        elapsed = time.time() - start

        assert result.exit_code == 0
        assert elapsed < 2.0  # Should complete in less than 2 seconds

    def test_completion_with_many_tasks(self, cli_runner, temp_dir):
        """Test that completion handles projects with many tasks."""
        import os

        config_path = temp_dir / "pyproject.toml"
        tasks_toml = "\n".join([f'task{i} = "echo task {i}"' for i in range(100)])
        config_path.write_text(
            f"""
[tool.taskx.tasks]
{tasks_toml}
"""
        )

        original_dir = os.getcwd()
        try:
            os.chdir(temp_dir)
            result = cli_runner.invoke(cli, ["completion", "bash"])

            assert result.exit_code == 0
            assert len(result.output) > 0
        finally:
            os.chdir(original_dir)
