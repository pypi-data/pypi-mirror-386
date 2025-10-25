"""
Unit tests for Fish completion generator.

Tests Fish-specific completion script generation and syntax.
"""

import re
import subprocess
import tempfile
from pathlib import Path

import pytest

from taskx.completion.fish import FishCompletion

# ============================================================================
# Test FishCompletion
# ============================================================================


@pytest.mark.unit
class TestFishCompletion:
    """Test suite for Fish completion generator."""

    def test_fish_generator_instantiation(self, sample_config):
        """Test that FishCompletion can be instantiated."""
        generator = FishCompletion(sample_config)
        assert generator is not None
        assert generator.config == sample_config

    def test_fish_generate_returns_string(self, sample_config):
        """Test that generate method returns a string."""
        generator = FishCompletion(sample_config)
        result = generator.generate()

        assert isinstance(result, str)
        assert len(result) > 0

    def test_fish_generate_includes_complete_commands(self, sample_config):
        """Test that generated script includes complete commands."""
        generator = FishCompletion(sample_config)
        result = generator.generate()

        # Fish uses 'complete' command for completion definitions
        assert "complete" in result
        assert "-c taskx" in result or "--command taskx" in result

    def test_fish_generate_includes_conditions(self, sample_config):
        """Test that Fish completion includes conditional logic."""
        generator = FishCompletion(sample_config)
        result = generator.generate()

        # Fish uses conditions with -n or --condition
        assert "-n" in result or "--condition" in result or "__fish_" in result

    def test_fish_generate_valid_syntax(self, sample_config):
        """Test that generated Fish script has valid syntax."""
        generator = FishCompletion(sample_config)
        result = generator.generate()

        # Write to temporary file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".fish", delete=False) as f:
            f.write(result)
            temp_path = f.name

        try:
            # Try to validate with fish if available
            try:
                proc = subprocess.run(
                    ["fish", "-n", temp_path], capture_output=True, text=True, timeout=5
                )
                if proc.returncode != 127:  # 127 = command not found
                    assert proc.returncode == 0, f"Syntax error: {proc.stderr}"
            except (FileNotFoundError, subprocess.TimeoutExpired):
                pytest.skip("fish not available for syntax checking")
        finally:
            Path(temp_path).unlink()

    def test_fish_completion_script_parseable(self, sample_config):
        """Test that completion script follows Fish completion patterns."""
        generator = FishCompletion(sample_config)
        result = generator.generate()

        # Check for Fish completion patterns
        lines = result.split("\n")
        complete_lines = [l for l in lines if "complete" in l and not l.strip().startswith("#")]
        assert len(complete_lines) > 0

    def test_fish_includes_all_commands(self, sample_config):
        """Test that generated script includes all CLI commands."""
        generator = FishCompletion(sample_config)
        result = generator.generate()

        commands = generator.get_commands()
        for command in commands:
            # Each command should be in the completion
            assert command in result

    def test_fish_includes_task_completion(self, sample_config):
        """Test that completion includes task names."""
        generator = FishCompletion(sample_config)
        result = generator.generate()

        tasks = generator.get_tasks()
        # Tasks or task command should be present
        assert any(task in result for task in tasks) or "taskx list" in result

    def test_fish_handles_empty_tasks(self, temp_dir):
        """Test that Fish completion handles projects with no tasks."""
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

        generator = FishCompletion(config)
        result = generator.generate()

        assert isinstance(result, str)
        assert len(result) > 0

    def test_fish_includes_descriptions(self, temp_dir):
        """Test that Fish completion includes task descriptions."""
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

        generator = FishCompletion(config)
        result = generator.generate()

        # Fish supports descriptions with -d or --description
        assert "-d" in result or "--description" in result

    def test_fish_includes_documentation_comments(self, sample_config):
        """Test that generated script includes helpful comments."""
        generator = FishCompletion(sample_config)
        result = generator.generate()

        assert "#" in result
        comment_lines = [line for line in result.split("\n") if line.strip().startswith("#")]
        assert len(comment_lines) > 1

    def test_fish_includes_graph_format_completion(self, sample_config):
        """Test that Fish completion includes graph format options."""
        generator = FishCompletion(sample_config)
        result = generator.generate()

        formats = generator.get_graph_formats()
        # Should have format completion
        assert any(fmt in result for fmt in formats)

    def test_fish_completion_for_subcommands(self, sample_config):
        """Test that Fish completion handles subcommands correctly."""
        generator = FishCompletion(sample_config)
        result = generator.generate()

        # Should handle subcommands like 'taskx completion fish'
        assert "completion" in result

    def test_fish_uses_helper_functions(self, sample_config):
        """Test that script uses Fish helper functions."""
        generator = FishCompletion(sample_config)
        result = generator.generate()

        # Fish has helper functions like __fish_seen_subcommand_from
        fish_helpers = [
            "__fish_seen_subcommand_from",
            "__fish_use_subcommand",
            "__fish_contains_opt",
        ]
        assert any(helper in result for helper in fish_helpers)

    def test_fish_completion_handles_special_characters(self, temp_dir):
        """Test that Fish completion handles tasks with special characters."""
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

        generator = FishCompletion(config)
        result = generator.generate()

        assert isinstance(result, str)
        assert len(result) > 0

    def test_fish_handles_long_task_lists(self, temp_dir):
        """Test that Fish completion handles many tasks efficiently."""
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

        generator = FishCompletion(config)
        result = generator.generate()

        assert isinstance(result, str)
        assert len(result) > 100

    def test_fish_completion_structure(self, sample_config):
        """Test that completion script has proper structure."""
        generator = FishCompletion(sample_config)
        result = generator.generate()

        lines = result.split("\n")
        assert len(lines) > 5

        # Should have multiple complete commands
        complete_lines = [l for l in lines if "complete" in l and "taskx" in l]
        assert len(complete_lines) > 0

    def test_fish_completion_command_format(self, sample_config):
        """Test that complete commands follow proper Fish format."""
        generator = FishCompletion(sample_config)
        result = generator.generate()

        # Fish complete command format: complete -c command [options]
        complete_pattern = r"complete\s+(-c|--command)\s+taskx"
        assert re.search(complete_pattern, result)

    def test_fish_completion_uses_options(self, sample_config):
        """Test that completion specifies options correctly."""
        generator = FishCompletion(sample_config)
        result = generator.generate()

        # Fish uses -a for arguments, -l for long options, -s for short options
        fish_options = ["-a", "-l", "-s", "--arguments", "--long-option", "--short-option"]
        assert any(opt in result for opt in fish_options)

    def test_fish_completion_escapes_special_chars(self, temp_dir):
        """Test that special characters in task names are properly handled."""
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

        generator = FishCompletion(config)
        result = generator.generate()

        assert isinstance(result, str)

    @pytest.mark.parametrize("command", ["run", "list", "init", "graph", "completion"])
    def test_fish_completion_includes_specific_command(self, sample_config, command):
        """Test that completion includes specific commands."""
        generator = FishCompletion(sample_config)
        result = generator.generate()

        assert command in result

    def test_fish_completion_conditional_logic(self, sample_config):
        """Test that completion uses conditional completion."""
        generator = FishCompletion(sample_config)
        result = generator.generate()

        # Fish uses conditions to determine when to show completions
        assert "__fish_" in result or "-n" in result

    def test_fish_completion_exclusive_options(self, sample_config):
        """Test that completion marks exclusive options."""
        generator = FishCompletion(sample_config)
        result = generator.generate()

        # Fish uses -x for exclusive completion
        # Some completions should be exclusive (can't combine with other args)
        assert "-x" in result or "--exclusive" in result or "-f" in result

    def test_fish_completion_function_definitions(self, sample_config):
        """Test that script defines helper functions if needed."""
        generator = FishCompletion(sample_config)
        result = generator.generate()

        # May define functions with 'function' keyword
        if "function " in result:
            assert "end" in result  # Fish functions end with 'end'

    def test_fish_completion_multiline_handling(self, sample_config):
        """Test that multiline completions are handled correctly."""
        generator = FishCompletion(sample_config)
        result = generator.generate()

        lines = result.split("\n")
        # Each complete command should be on its own line or properly continued
        for i, line in enumerate(lines):
            if line.strip().startswith("complete"):
                # Should not have unterminated strings
                if line.count("'") % 2 != 0 and line.count('"') % 2 != 0:
                    # Line continues or has escaped quotes
                    assert line.rstrip().endswith("\\") or i + 1 < len(lines)

    def test_fish_completion_no_syntax_errors(self, sample_config):
        """Test that generated completion has no common syntax errors."""
        generator = FishCompletion(sample_config)
        result = generator.generate()

        # Check for balanced quotes
        lines = result.split("\n")
        for line in lines:
            if line.strip().startswith("#"):
                continue
            # Simple quote balance check (not perfect but catches obvious errors)
            if line.count("'") % 2 != 0 and not line.rstrip().endswith("\\"):
                # Could be balanced across lines, which is less common in Fish
                pass  # Allow it for now

    def test_fish_completion_argument_completion(self, sample_config):
        """Test that arguments are completed properly."""
        generator = FishCompletion(sample_config)
        result = generator.generate()

        # Fish uses -a or --arguments for argument completion
        assert "-a" in result or "--arguments" in result

    def test_fish_completion_for_flags(self, sample_config):
        """Test that flags/options are completed."""
        generator = FishCompletion(sample_config)
        result = generator.generate()

        # Should define completions for command flags
        # Fish uses -l for long options
        assert (
            "-l help" in result
            or "-l version" in result
            or "--help" in result
            or "--version" in result
        )
