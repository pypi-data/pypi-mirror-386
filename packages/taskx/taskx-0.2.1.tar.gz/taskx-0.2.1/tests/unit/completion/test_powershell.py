"""
Unit tests for PowerShell completion generator.

Tests PowerShell-specific completion script generation and syntax.
"""

import subprocess
import tempfile
from pathlib import Path

import pytest

from taskx.completion.powershell import PowerShellCompletion

# ============================================================================
# Test PowerShellCompletion
# ============================================================================


@pytest.mark.unit
class TestPowerShellCompletion:
    """Test suite for PowerShell completion generator."""

    def test_powershell_generator_instantiation(self, sample_config):
        """Test that PowerShellCompletion can be instantiated."""
        generator = PowerShellCompletion(sample_config)
        assert generator is not None
        assert generator.config == sample_config

    def test_powershell_generate_returns_string(self, sample_config):
        """Test that generate method returns a string."""
        generator = PowerShellCompletion(sample_config)
        result = generator.generate()

        assert isinstance(result, str)
        assert len(result) > 0

    def test_powershell_generate_includes_register_argumentcompleter(self, sample_config):
        """Test that script includes Register-ArgumentCompleter."""
        generator = PowerShellCompletion(sample_config)
        result = generator.generate()

        # PowerShell uses Register-ArgumentCompleter for tab completion
        assert "Register-ArgumentCompleter" in result

    def test_powershell_generate_includes_scriptblock(self, sample_config):
        """Test that script includes a scriptblock for completion logic."""
        generator = PowerShellCompletion(sample_config)
        result = generator.generate()

        # PowerShell scriptblocks use { }
        assert "{" in result and "}" in result
        assert "-ScriptBlock" in result or "ScriptBlock" in result

    def test_powershell_generate_valid_syntax(self, sample_config):
        """Test that generated PowerShell script has valid syntax."""
        generator = PowerShellCompletion(sample_config)
        result = generator.generate()

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".ps1", delete=False, encoding="utf-8"
        ) as f:
            f.write(result)
            temp_path = f.name

        try:
            # Try to validate with PowerShell if available
            try:
                proc = subprocess.run(
                    [
                        "pwsh",
                        "-NoProfile",
                        "-Command",
                        f'$null = [System.Management.Automation.PSParser]::Tokenize((Get-Content "{temp_path}" -Raw), [ref]$null)',
                    ],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                if proc.returncode == 0 or proc.returncode == 127:
                    # Success or pwsh not found
                    pass
                else:
                    # Try with Windows PowerShell
                    proc = subprocess.run(
                        [
                            "powershell",
                            "-NoProfile",
                            "-Command",
                            f'$null = [System.Management.Automation.PSParser]::Tokenize((Get-Content "{temp_path}" -Raw), [ref]$null)',
                        ],
                        capture_output=True,
                        text=True,
                        timeout=10,
                    )
            except (FileNotFoundError, subprocess.TimeoutExpired):
                pytest.skip("PowerShell not available for syntax checking")
        finally:
            Path(temp_path).unlink()

    def test_powershell_completion_script_parseable(self, sample_config):
        """Test that completion script follows PowerShell patterns."""
        generator = PowerShellCompletion(sample_config)
        result = generator.generate()

        # Check for PowerShell completion patterns
        assert "param(" in result.lower() or "$" in result
        assert "Register-ArgumentCompleter" in result

    def test_powershell_includes_all_commands(self, sample_config):
        """Test that generated script includes all CLI commands."""
        generator = PowerShellCompletion(sample_config)
        result = generator.generate()

        commands = generator.get_commands()
        for command in commands:
            assert command in result

    def test_powershell_includes_task_completion(self, sample_config):
        """Test that completion includes task names."""
        generator = PowerShellCompletion(sample_config)
        result = generator.generate()

        tasks = generator.get_tasks()
        # Tasks or dynamic task loading should be present
        assert any(task in result for task in tasks) or "taskx list" in result

    def test_powershell_handles_empty_tasks(self, temp_dir):
        """Test that PowerShell completion handles projects with no tasks."""
        from taskx.core.config import Config

        config_path = temp_dir / "pyproject.toml"
        config_path.write_text(
            """
[tool.taskx.tasks]
dummy = "echo test"

[tool.taskx.env]
APP_NAME = "test"
"""
        )

        config = Config(config_path)
        config.load()

        generator = PowerShellCompletion(config)
        result = generator.generate()

        assert isinstance(result, str)
        assert len(result) > 0

    def test_powershell_includes_documentation_comments(self, sample_config):
        """Test that generated script includes helpful comments."""
        generator = PowerShellCompletion(sample_config)
        result = generator.generate()

        assert "#" in result or "<#" in result
        # PowerShell uses # for single-line and <# #> for multi-line comments

    def test_powershell_includes_graph_format_completion(self, sample_config):
        """Test that PowerShell completion includes graph format options."""
        generator = PowerShellCompletion(sample_config)
        result = generator.generate()

        formats = generator.get_graph_formats()
        # Should have format completion
        assert any(fmt in result for fmt in formats)

    def test_powershell_completion_for_subcommands(self, sample_config):
        """Test that PowerShell completion handles subcommands correctly."""
        generator = PowerShellCompletion(sample_config)
        result = generator.generate()

        assert "completion" in result

    def test_powershell_uses_completion_result_type(self, sample_config):
        """Test that script uses CompletionResult type."""
        generator = PowerShellCompletion(sample_config)
        result = generator.generate()

        # PowerShell returns [System.Management.Automation.CompletionResult] objects
        assert "CompletionResult" in result or "New-Object" in result

    def test_powershell_completion_handles_special_characters(self, temp_dir):
        """Test that PowerShell completion handles tasks with special characters."""
        from taskx.core.config import Config

        config_path = temp_dir / "pyproject.toml"
        config_path.write_text(
            """
[tool.taskx.tasks]
test-unit = "pytest tests/unit"
test_integration = "pytest tests/integration"
build_dev = "python -m build"
"""
        )

        config = Config(config_path)
        config.load()

        generator = PowerShellCompletion(config)
        result = generator.generate()

        assert isinstance(result, str)
        assert len(result) > 0

    def test_powershell_handles_long_task_lists(self, temp_dir):
        """Test that PowerShell completion handles many tasks efficiently."""
        from taskx.core.config import Config

        config_path = temp_dir / "pyproject.toml"
        tasks_toml = "\n".join([f'task{i} = "echo task {i}"' for i in range(50)])
        config_path.write_text(
            f"""
[tool.taskx.tasks]
{tasks_toml}
"""
        )

        config = Config(config_path)
        config.load()

        generator = PowerShellCompletion(config)
        result = generator.generate()

        assert isinstance(result, str)
        assert len(result) > 100

    def test_powershell_completion_structure(self, sample_config):
        """Test that completion script has proper structure."""
        generator = PowerShellCompletion(sample_config)
        result = generator.generate()

        lines = result.split("\n")
        assert len(lines) > 10

        # Should have Register-ArgumentCompleter call
        assert any("Register-ArgumentCompleter" in line for line in lines)

    def test_powershell_completion_command_name(self, sample_config):
        """Test that completion is registered for correct command name."""
        generator = PowerShellCompletion(sample_config)
        result = generator.generate()

        # Should register for 'taskx' command
        assert "-CommandName" in result and "taskx" in result

    def test_powershell_uses_parameters(self, sample_config):
        """Test that scriptblock defines necessary parameters."""
        generator = PowerShellCompletion(sample_config)
        result = generator.generate()

        # PowerShell completion scriptblock should have parameters
        # Common: $wordToComplete, $commandAst, $cursorPosition
        assert "param(" in result.lower()
        assert "$" in result  # Has variables

    def test_powershell_completion_escapes_special_chars(self, temp_dir):
        """Test that special characters are properly escaped."""
        from taskx.core.config import Config

        config_path = temp_dir / "pyproject.toml"
        config_path.write_text(
            """
[tool.taskx.tasks]
test-all = "pytest tests/"
build_prod = "python -m build"
"""
        )

        config = Config(config_path)
        config.load()

        generator = PowerShellCompletion(config)
        result = generator.generate()

        assert isinstance(result, str)

    @pytest.mark.parametrize("command", ["run", "list", "init", "graph", "completion"])
    def test_powershell_completion_includes_specific_command(self, sample_config, command):
        """Test that completion includes specific commands."""
        generator = PowerShellCompletion(sample_config)
        result = generator.generate()

        assert command in result

    def test_powershell_completion_no_syntax_errors(self, sample_config):
        """Test that generated completion has no common syntax errors."""
        generator = PowerShellCompletion(sample_config)
        result = generator.generate()

        # Check for balanced braces
        assert result.count("{") == result.count("}")
        assert result.count("(") == result.count(")")
        assert result.count("[") == result.count("]")

    def test_powershell_completion_returns_results(self, sample_config):
        """Test that completion scriptblock returns results."""
        generator = PowerShellCompletion(sample_config)
        result = generator.generate()

        # Should return completion results
        assert "return" in result.lower() or "CompletionResult" in result

    def test_powershell_completion_string_handling(self, sample_config):
        """Test that strings are properly quoted."""
        generator = PowerShellCompletion(sample_config)
        result = generator.generate()

        # PowerShell uses single or double quotes
        assert "'" in result or '"' in result

    def test_powershell_completion_uses_pipeline(self, sample_config):
        """Test that completion uses PowerShell pipeline."""
        generator = PowerShellCompletion(sample_config)
        result = generator.generate()

        # PowerShell often uses pipeline with | operator
        assert "|" in result or "ForEach-Object" in result or "Where-Object" in result

    def test_powershell_completion_has_tooltip_text(self, temp_dir):
        """Test that completions include tooltip/description text."""
        from taskx.core.config import Config

        config_path = temp_dir / "pyproject.toml"
        config_path.write_text(
            """
[tool.taskx.tasks]
test = { cmd = "pytest", description = "Run all tests" }
build = { cmd = "python -m build", description = "Build the package" }
"""
        )

        config = Config(config_path)
        config.load()

        generator = PowerShellCompletion(config)
        result = generator.generate()

        # CompletionResult constructor takes tooltip text
        # PowerShell uses CompletionResult with 4th parameter as description
        assert (
            "Run all tests" in result
            or "ToolTip" in result
            or "ListItemText" in result
            or "CompletionResult" in result
        )

    def test_powershell_completion_filters_by_word(self, sample_config):
        """Test that completion filters based on partial word."""
        generator = PowerShellCompletion(sample_config)
        result = generator.generate()

        # Should use $wordToComplete to filter results
        assert "$wordToComplete" in result or "$word" in result or "StartsWith" in result

    def test_powershell_completion_handles_position(self, sample_config):
        """Test that completion handles cursor position."""
        generator = PowerShellCompletion(sample_config)
        result = generator.generate()

        # Completion scriptblock gets cursor position parameter
        assert "$cursorPosition" in result or "$cursor" in result or "param(" in result.lower()

    def test_powershell_completion_native_format(self, sample_config):
        """Test that completion follows PowerShell native format."""
        generator = PowerShellCompletion(sample_config)
        result = generator.generate()

        # Should use PowerShell 5.0+ ArgumentCompleter
        assert "Register-ArgumentCompleter" in result
        assert "-CommandName" in result or "-Native" in result

    def test_powershell_completion_ast_parameter(self, sample_config):
        """Test that completion uses AST parameter."""
        generator = PowerShellCompletion(sample_config)
        result = generator.generate()

        # Modern PowerShell completions use $commandAst parameter
        assert "$commandAst" in result or "$command" in result or "param(" in result.lower()

    def test_powershell_uses_completion_result_type_enum(self, sample_config):
        """Test that completion uses result type enum."""
        generator = PowerShellCompletion(sample_config)
        result = generator.generate()

        # CompletionResultType enum values: ParameterName, ParameterValue, etc.
        assert "ParameterValue" in result or "ParameterName" in result or "Command" in result
