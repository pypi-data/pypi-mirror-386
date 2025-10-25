"""
Unit tests for base completion generator.

Tests the abstract base class and common functionality for all completion generators.
"""

from unittest.mock import Mock

import pytest

from taskx.completion.base import CompletionGenerator
from taskx.core.config import Config

# ============================================================================
# Concrete Implementation for Testing
# ============================================================================


class ConcreteCompletionGenerator(CompletionGenerator):
    """Concrete implementation for testing abstract base class."""

    def generate(self) -> str:
        """Generate completion script."""
        return "# Test completion script"


# ============================================================================
# Test CompletionGenerator Base Class
# ============================================================================


class TestCompletionGenerator:
    """Test suite for CompletionGenerator abstract base class."""

    def test_cannot_instantiate_abstract_class(self):
        """Test that CompletionGenerator cannot be instantiated directly."""
        with pytest.raises(TypeError):
            CompletionGenerator(Mock(spec=Config))

    def test_concrete_implementation_can_be_instantiated(self):
        """Test that concrete implementation can be instantiated."""
        config = Mock(spec=Config)
        generator = ConcreteCompletionGenerator(config)
        assert generator is not None
        assert generator.config == config

    def test_get_tasks_returns_sorted_list(self, sample_config):
        """Test that get_tasks returns a sorted list of task names."""
        generator = ConcreteCompletionGenerator(sample_config)
        tasks = generator.get_tasks()

        assert isinstance(tasks, list)
        assert len(tasks) > 0
        assert all(isinstance(task, str) for task in tasks)
        # Verify sorted order
        assert tasks == sorted(tasks)

    def test_get_tasks_includes_all_defined_tasks(self, sample_config):
        """Test that get_tasks includes all tasks from config."""
        generator = ConcreteCompletionGenerator(sample_config)
        tasks = generator.get_tasks()

        # Sample config should have these tasks
        expected_tasks = ["build", "deploy", "hello", "test"]
        assert all(task in tasks for task in expected_tasks)

    def test_get_commands_returns_correct_commands(self):
        """Test that get_commands returns the correct list of CLI commands."""
        config = Mock(spec=Config)
        generator = ConcreteCompletionGenerator(config)
        commands = generator.get_commands()

        assert isinstance(commands, list)
        assert len(commands) > 0
        assert all(isinstance(cmd, str) for cmd in commands)

        # Check for expected core commands
        expected_commands = ["run", "list", "init", "graph", "completion"]
        assert all(cmd in commands for cmd in expected_commands)

    def test_get_graph_formats_returns_valid_formats(self):
        """Test that get_graph_formats returns valid graph output formats."""
        config = Mock(spec=Config)
        generator = ConcreteCompletionGenerator(config)
        formats = generator.get_graph_formats()

        assert isinstance(formats, list)
        assert len(formats) > 0
        assert all(isinstance(fmt, str) for fmt in formats)

        # Check for expected formats
        expected_formats = ["tree", "dot", "mermaid"]
        assert all(fmt in formats for fmt in expected_formats)

    def test_abstract_generate_raises_not_implemented(self):
        """Test that abstract generate method raises NotImplementedError."""

        # Create a class that doesn't implement generate
        class IncompleteGenerator(CompletionGenerator):
            pass

        with pytest.raises(TypeError):
            config = Mock(spec=Config)
            IncompleteGenerator(config)

    def test_get_tasks_handles_empty_config(self, temp_dir):
        """Test that get_tasks handles config with no tasks gracefully."""

        # Create config with minimal task (config requires at least one task)
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

        generator = ConcreteCompletionGenerator(config)
        tasks = generator.get_tasks()

        assert isinstance(tasks, list)
        assert len(tasks) >= 1

    def test_generator_stores_config_reference(self, sample_config):
        """Test that generator stores reference to config."""
        generator = ConcreteCompletionGenerator(sample_config)

        assert generator.config is sample_config
        assert isinstance(generator.config, Config)

    def test_get_tasks_with_complex_task_names(self, temp_dir):
        """Test that get_tasks handles complex task names correctly."""

        config_path = temp_dir / "pyproject.toml"
        config_path.write_text(
            """
[tool.taskx.tasks]
test-unit = "pytest tests/unit"
test-integration = "pytest tests/integration"
build-dev = "python -m build"
build-prod = "python -m build --no-isolation"
"""
        )

        config = Config(config_path)
        config.load()

        generator = ConcreteCompletionGenerator(config)
        tasks = generator.get_tasks()

        expected_tasks = ["build-dev", "build-prod", "test-integration", "test-unit"]
        assert tasks == expected_tasks

    def test_generate_method_returns_string(self, sample_config):
        """Test that generate method returns a string."""
        generator = ConcreteCompletionGenerator(sample_config)
        result = generator.generate()

        assert isinstance(result, str)
        assert len(result) > 0

    @pytest.mark.parametrize("task_count", [1, 5, 20, 100])
    def test_get_tasks_performance(self, temp_dir, task_count):
        """Test that get_tasks performs well with various task counts."""
        import time

        # Create config with specified number of tasks (minimum 1 required)
        config_path = temp_dir / "pyproject.toml"
        tasks_toml = "\n".join([f'task{i} = "echo {i}"' for i in range(task_count)])
        config_path.write_text(
            f"""
[tool.taskx.tasks]
{tasks_toml}
"""
        )

        config = Config(config_path)
        config.load()

        generator = ConcreteCompletionGenerator(config)

        start = time.time()
        tasks = generator.get_tasks()
        elapsed = time.time() - start

        assert len(tasks) == task_count
        assert elapsed < 0.1  # Should complete in < 100ms

    def test_inheritance_structure(self):
        """Test that completion generator has correct inheritance."""
        from abc import ABC

        assert issubclass(CompletionGenerator, ABC)
        assert issubclass(ConcreteCompletionGenerator, CompletionGenerator)

    def test_config_passed_to_constructor(self, sample_config):
        """Test that config is correctly passed to constructor."""
        generator = ConcreteCompletionGenerator(sample_config)

        # Verify we can access config properties
        assert hasattr(generator.config, "load")
        assert hasattr(generator.config, "tasks")
