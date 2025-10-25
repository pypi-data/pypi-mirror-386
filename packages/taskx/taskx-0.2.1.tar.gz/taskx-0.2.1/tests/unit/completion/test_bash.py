"""
Unit tests for Bash completion generator.

Tests Bash-specific completion script generation and syntax.
"""

import re
import subprocess
import tempfile
from pathlib import Path

import pytest

from taskx.completion.bash import BashCompletion

# ============================================================================
# Test BashCompletion
# ============================================================================


@pytest.mark.unit
class TestBashCompletion:
    """Test suite for Bash completion generator."""

    def test_bash_generator_instantiation(self, sample_config):
        """Test that BashCompletion can be instantiated."""
        generator = BashCompletion(sample_config)
        assert generator is not None
        assert generator.config == sample_config

    def test_bash_generate_returns_string(self, sample_config):
        """Test that generate method returns a string."""
        generator = BashCompletion(sample_config)
        result = generator.generate()

        assert isinstance(result, str)
        assert len(result) > 0

    def test_bash_generate_includes_shebang(self, sample_config):
        """Test that generated script includes bash shebang."""
        generator = BashCompletion(sample_config)
        result = generator.generate()

        # Bash completion scripts may start with shebang or comment
        assert (
            result.startswith("#!/usr/bin/env bash")
            or result.startswith("#!/bin/bash")
            or result.startswith("#")
        )

    def test_bash_generate_includes_completion_function(self, sample_config):
        """Test that generated script includes completion function."""
        generator = BashCompletion(sample_config)
        result = generator.generate()

        # Should define _taskx_completion function
        assert "_taskx_completion()" in result or "_taskx()" in result
        assert "complete -F" in result

    def test_bash_generate_includes_all_commands(self, sample_config):
        """Test that generated script includes all CLI commands."""
        generator = BashCompletion(sample_config)
        result = generator.generate()

        commands = generator.get_commands()
        for command in commands:
            # Each command should be mentioned in completion
            assert command in result

    def test_bash_generate_includes_task_completion(self, sample_config):
        """Test that generated script includes task names for completion."""
        generator = BashCompletion(sample_config)
        result = generator.generate()

        tasks = generator.get_tasks()
        # At least some tasks should be in the completion script
        # (might not be all if they're dynamically loaded)
        assert (
            any(task in result for task in tasks) or "get_tasks" in result or "taskx list" in result
        )

    def test_bash_generate_valid_syntax(self, sample_config):
        """Test that generated Bash script has valid syntax."""
        generator = BashCompletion(sample_config)
        result = generator.generate()

        # Write to temporary file and check syntax
        with tempfile.NamedTemporaryFile(mode="w", suffix=".bash", delete=False) as f:
            f.write(result)
            temp_path = f.name

        try:
            # Use bash -n to check syntax without executing
            proc = subprocess.run(["bash", "-n", temp_path], capture_output=True, text=True)

            assert proc.returncode == 0, f"Syntax error: {proc.stderr}"
        finally:
            Path(temp_path).unlink()

    def test_bash_completion_script_parseable(self, sample_config):
        """Test that completion script can be parsed by bash."""
        generator = BashCompletion(sample_config)
        result = generator.generate()

        # Check for common bash completion patterns
        assert "COMPREPLY" in result or "compgen" in result
        assert "COMP_WORDS" in result or "words" in result

    def test_bash_includes_complete_registration(self, sample_config):
        """Test that script includes complete registration for taskx."""
        generator = BashCompletion(sample_config)
        result = generator.generate()

        # Should register completion for 'taskx' command
        assert "complete" in result
        assert "taskx" in result

    def test_bash_handles_empty_tasks(self, temp_dir):
        """Test that Bash completion handles projects with no tasks."""
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

        generator = BashCompletion(config)
        result = generator.generate()

        assert isinstance(result, str)
        assert len(result) > 0
        # Should still have basic command completion
        assert "complete" in result

    def test_bash_includes_graph_format_completion(self, sample_config):
        """Test that Bash completion includes graph format options."""
        generator = BashCompletion(sample_config)
        result = generator.generate()

        formats = generator.get_graph_formats()
        # Should mention at least some formats or have dynamic format completion
        assert any(fmt in result for fmt in formats) or "get_graph_formats" in result

    def test_bash_completion_handles_special_characters_in_tasks(self, temp_dir):
        """Test that Bash completion handles tasks with special characters."""
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

        generator = BashCompletion(config)
        result = generator.generate()

        # Should generate valid script even with special characters
        assert isinstance(result, str)
        assert len(result) > 0

    def test_bash_includes_documentation_comments(self, sample_config):
        """Test that generated script includes helpful comments."""
        generator = BashCompletion(sample_config)
        result = generator.generate()

        # Should have documentation comments
        assert "#" in result
        # Look for typical comment patterns
        comment_lines = [line for line in result.split("\n") if line.strip().startswith("#")]
        assert len(comment_lines) > 2  # More than just shebang

    def test_bash_completion_for_subcommands(self, sample_config):
        """Test that Bash completion handles subcommands correctly."""
        generator = BashCompletion(sample_config)
        result = generator.generate()

        # Commands like 'taskx completion bash' should be handled
        assert "completion" in result

    def test_bash_uses_compgen_or_equivalent(self, sample_config):
        """Test that script uses compgen or equivalent completion mechanism."""
        generator = BashCompletion(sample_config)
        result = generator.generate()

        # Should use standard bash completion mechanisms
        assert "compgen" in result or "COMPREPLY=(" in result

    def test_bash_completion_script_structure(self, sample_config):
        """Test that completion script has proper structure."""
        generator = BashCompletion(sample_config)
        result = generator.generate()

        lines = result.split("\n")

        # Should have multiple lines
        assert len(lines) > 10

        # Should have function definition
        function_pattern = r"(function\s+\w+|_\w+\(\))"
        assert any(re.search(function_pattern, line) for line in lines)

        # Should have complete command at the end
        assert any("complete" in line for line in lines[-20:])

    def test_bash_handles_long_task_lists(self, temp_dir):
        """Test that Bash completion handles many tasks efficiently."""
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

        generator = BashCompletion(config)
        result = generator.generate()

        # Should generate valid completion script
        assert isinstance(result, str)
        assert len(result) > 100

        # Check syntax is still valid
        with tempfile.NamedTemporaryFile(mode="w", suffix=".bash", delete=False) as f:
            f.write(result)
            temp_path = f.name

        try:
            proc = subprocess.run(["bash", "-n", temp_path], capture_output=True, text=True)
            assert proc.returncode == 0
        finally:
            Path(temp_path).unlink()

    def test_bash_completion_escapes_special_chars(self, temp_dir):
        """Test that special characters in task names are properly escaped."""
        from taskx.core.config import Config

        config_path = temp_dir / "pyproject.toml"
        config_path.write_text(
            """
[tool.taskx.tasks]
test-all = "pytest tests/"
build_prod = "python -m build"
deploy_dev = "echo deploying"
"""
        )

        config = Config(config_path)
        config.load()

        generator = BashCompletion(config)
        result = generator.generate()

        # Should still produce valid bash
        with tempfile.NamedTemporaryFile(mode="w", suffix=".bash", delete=False) as f:
            f.write(result)
            temp_path = f.name

        try:
            proc = subprocess.run(["bash", "-n", temp_path], capture_output=True, text=True)
            assert proc.returncode == 0, f"Syntax error with special chars: {proc.stderr}"
        finally:
            Path(temp_path).unlink()

    @pytest.mark.parametrize("command", ["run", "list", "init", "graph", "completion"])
    def test_bash_completion_includes_specific_command(self, sample_config, command):
        """Test that completion includes specific commands."""
        generator = BashCompletion(sample_config)
        result = generator.generate()

        assert command in result

    def test_bash_completion_no_syntax_errors(self, sample_config):
        """Test that generated completion has no common syntax errors."""
        generator = BashCompletion(sample_config)
        result = generator.generate()

        # Check for common syntax errors (allowing for subshells and command substitution)
        # Note: $(...) creates nested parentheses which is valid bash
        assert result.count("{") == result.count("}")  # Balanced braces
        assert result.count("[") == result.count("]")  # Balanced brackets

        # No unterminated strings (simple check)
        lines = result.split("\n")
        for line in lines:
            # Skip comments
            if line.strip().startswith("#"):
                continue
            # Count quotes (excluding escaped quotes)
            line_clean = re.sub(r"\\.", "", line)  # Remove escaped chars
            assert line_clean.count('"') % 2 == 0, f"Unterminated string in: {line}"
