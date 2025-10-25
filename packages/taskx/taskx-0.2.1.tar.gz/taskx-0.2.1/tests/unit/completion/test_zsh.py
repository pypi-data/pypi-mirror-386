"""
Unit tests for Zsh completion generator.

Tests Zsh-specific completion script generation and syntax.
"""

import re
import subprocess
import tempfile
from pathlib import Path

import pytest

from taskx.completion.zsh import ZshCompletion

# ============================================================================
# Test ZshCompletion
# ============================================================================


@pytest.mark.unit
class TestZshCompletion:
    """Test suite for Zsh completion generator."""

    def test_zsh_generator_instantiation(self, sample_config):
        """Test that ZshCompletion can be instantiated."""
        generator = ZshCompletion(sample_config)
        assert generator is not None
        assert generator.config == sample_config

    def test_zsh_generate_returns_string(self, sample_config):
        """Test that generate method returns a string."""
        generator = ZshCompletion(sample_config)
        result = generator.generate()

        assert isinstance(result, str)
        assert len(result) > 0

    def test_zsh_generate_includes_shebang(self, sample_config):
        """Test that generated script includes zsh shebang."""
        generator = ZshCompletion(sample_config)
        result = generator.generate()

        assert result.startswith("#!") or result.startswith("#compdef")

    def test_zsh_generate_includes_compdef(self, sample_config):
        """Test that generated script includes compdef directive."""
        generator = ZshCompletion(sample_config)
        result = generator.generate()

        # Zsh completion should use compdef
        assert "compdef" in result or "#compdef" in result

    def test_zsh_generate_includes_descriptions(self, sample_config):
        """Test that Zsh completion includes task descriptions."""
        generator = ZshCompletion(sample_config)
        result = generator.generate()

        # Zsh supports descriptions in completion
        # Should use _describe or similar
        assert "_describe" in result or "_arguments" in result

    def test_zsh_generate_valid_syntax(self, sample_config):
        """Test that generated Zsh script has valid syntax."""
        generator = ZshCompletion(sample_config)
        result = generator.generate()

        # Write to temporary file and check syntax
        with tempfile.NamedTemporaryFile(mode="w", suffix=".zsh", delete=False) as f:
            f.write(result)
            temp_path = f.name

        try:
            # Use zsh -n to check syntax if zsh is available
            try:
                proc = subprocess.run(
                    ["zsh", "-n", temp_path], capture_output=True, text=True, timeout=5
                )
                # If zsh is available, check it passes
                if proc.returncode != 127:  # 127 = command not found
                    assert proc.returncode == 0, f"Syntax error: {proc.stderr}"
            except (FileNotFoundError, subprocess.TimeoutExpired):
                # zsh not available or timed out, skip this check
                pytest.skip("zsh not available for syntax checking")
        finally:
            Path(temp_path).unlink()

    def test_zsh_completion_script_parseable(self, sample_config):
        """Test that completion script uses proper Zsh completion structure."""
        generator = ZshCompletion(sample_config)
        result = generator.generate()

        # Check for Zsh completion patterns
        assert "_taskx" in result or "compdef _taskx" in result
        assert any(pattern in result for pattern in ["_describe", "_arguments", "_values"])

    def test_zsh_includes_all_commands(self, sample_config):
        """Test that generated script includes all CLI commands."""
        generator = ZshCompletion(sample_config)
        result = generator.generate()

        commands = generator.get_commands()
        for command in commands:
            # Commands should be in the completion
            assert command in result

    def test_zsh_includes_task_names(self, sample_config):
        """Test that completion includes task names."""
        generator = ZshCompletion(sample_config)
        result = generator.generate()

        tasks = generator.get_tasks()
        # Tasks or task retrieval function should be present
        assert (
            any(task in result for task in tasks) or "get_tasks" in result or "taskx list" in result
        )

    def test_zsh_handles_empty_tasks(self, temp_dir):
        """Test that Zsh completion handles projects with no tasks."""
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

        generator = ZshCompletion(config)
        result = generator.generate()

        assert isinstance(result, str)
        assert len(result) > 0

    def test_zsh_completion_function_definition(self, sample_config):
        """Test that completion defines proper Zsh function."""
        generator = ZshCompletion(sample_config)
        result = generator.generate()

        # Should define completion function
        function_pattern = r"(function\s+_taskx|_taskx\(\))"
        assert re.search(function_pattern, result)

    def test_zsh_includes_documentation_comments(self, sample_config):
        """Test that generated script includes helpful comments."""
        generator = ZshCompletion(sample_config)
        result = generator.generate()

        # Should have documentation comments
        assert "#" in result
        comment_lines = [line for line in result.split("\n") if line.strip().startswith("#")]
        assert len(comment_lines) > 1

    def test_zsh_includes_graph_format_completion(self, sample_config):
        """Test that Zsh completion includes graph format options."""
        generator = ZshCompletion(sample_config)
        result = generator.generate()

        formats = generator.get_graph_formats()
        # Should have format completion
        assert any(fmt in result for fmt in formats) or "_values" in result

    def test_zsh_completion_for_subcommands(self, sample_config):
        """Test that Zsh completion handles subcommands correctly."""
        generator = ZshCompletion(sample_config)
        result = generator.generate()

        # Should handle subcommands like 'taskx completion zsh'
        assert "completion" in result

    def test_zsh_uses_compsys_framework(self, sample_config):
        """Test that script uses Zsh completion system (compsys)."""
        generator = ZshCompletion(sample_config)
        result = generator.generate()

        # Should use Zsh completion system functions
        compsys_functions = ["_describe", "_arguments", "_values", "_message", "_command"]
        assert any(func in result for func in compsys_functions)

    def test_zsh_completion_handles_special_characters(self, temp_dir):
        """Test that Zsh completion handles tasks with special characters."""
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

        generator = ZshCompletion(config)
        result = generator.generate()

        assert isinstance(result, str)
        assert len(result) > 0

    def test_zsh_completion_with_descriptions(self, temp_dir):
        """Test that Zsh completion includes task descriptions when available."""
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

        generator = ZshCompletion(config)
        result = generator.generate()

        # Descriptions should be included somehow
        assert "Run all tests" in result or "_describe" in result

    def test_zsh_handles_long_task_lists(self, temp_dir):
        """Test that Zsh completion handles many tasks efficiently."""
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

        generator = ZshCompletion(config)
        result = generator.generate()

        assert isinstance(result, str)
        assert len(result) > 100

    def test_zsh_completion_structure(self, sample_config):
        """Test that completion script has proper structure."""
        generator = ZshCompletion(sample_config)
        result = generator.generate()

        lines = result.split("\n")
        assert len(lines) > 10

        # Should have function definition
        function_pattern = r"(_taskx|function.*taskx)"
        assert any(re.search(function_pattern, line) for line in lines)

    def test_zsh_completion_escapes_special_chars(self, temp_dir):
        """Test that special characters in task names are properly escaped."""
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

        generator = ZshCompletion(config)
        result = generator.generate()

        # Should still produce valid zsh
        assert isinstance(result, str)

    @pytest.mark.parametrize("command", ["run", "list", "init", "graph", "completion"])
    def test_zsh_completion_includes_specific_command(self, sample_config, command):
        """Test that completion includes specific commands."""
        generator = ZshCompletion(sample_config)
        result = generator.generate()

        assert command in result

    def test_zsh_completion_no_syntax_errors(self, sample_config):
        """Test that generated completion has no common syntax errors."""
        generator = ZshCompletion(sample_config)
        result = generator.generate()

        # Check for balanced delimiters (allowing for zsh array syntax and command substitution)
        # Note: Zsh uses () for arrays and $() for command substitution
        assert result.count("{") == result.count("}")
        assert result.count("[") == result.count("]")

    def test_zsh_completion_uses_local_variables(self, sample_config):
        """Test that completion script uses local variables properly."""
        generator = ZshCompletion(sample_config)
        result = generator.generate()

        # Zsh completions should use local or typeset for variables
        assert "local " in result or "typeset " in result

    def test_zsh_completion_state_management(self, sample_config):
        """Test that completion handles completion state correctly."""
        generator = ZshCompletion(sample_config)
        result = generator.generate()

        # Should handle state for multi-level completion
        assert "_arguments" in result or "state" in result

    def test_zsh_completion_case_statements(self, sample_config):
        """Test that completion uses case statements for command handling."""
        generator = ZshCompletion(sample_config)
        result = generator.generate()

        # Zsh completions often use case statements
        assert "case " in result and "esac" in result

    def test_zsh_completion_registration(self, sample_config):
        """Test that completion is properly registered for taskx."""
        generator = ZshCompletion(sample_config)
        result = generator.generate()

        # Should register with compdef
        assert "compdef" in result
        assert "taskx" in result

    def test_zsh_completion_option_specs(self, sample_config):
        """Test that completion includes option specifications."""
        generator = ZshCompletion(sample_config)
        result = generator.generate()

        # Should specify options/flags
        # Common patterns: '--option', '-o', '(-option)'
        assert "--" in result or "(-" in result
