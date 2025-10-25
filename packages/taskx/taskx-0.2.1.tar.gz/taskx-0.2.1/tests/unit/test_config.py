"""Tests for config module."""

import pytest

from taskx.core.config import Config, ConfigError


class TestConfig:
    """Test Config class."""

    def test_load_config(self, sample_config_file):
        """Test loading configuration from file."""
        config = Config(sample_config_file)
        config.load()

        assert len(config.tasks) == 4
        assert "hello" in config.tasks
        assert "test" in config.tasks
        assert "build" in config.tasks
        assert "deploy" in config.tasks

    def test_load_env_vars(self, sample_config_file):
        """Test loading environment variables."""
        config = Config(sample_config_file)
        config.load()

        assert config.env["APP_NAME"] == "testapp"
        assert config.env["VERSION"] == "1.0.0"

    def test_get_task(self, sample_config):
        """Test getting a task by name."""
        task = sample_config.get_task("hello")
        assert task is not None
        assert task.name == "hello"
        assert task.cmd == "echo 'Hello, World!'"

    def test_get_nonexistent_task(self, sample_config):
        """Test getting non-existent task returns None."""
        task = sample_config.get_task("nonexistent")
        assert task is None

    def test_has_task(self, sample_config):
        """Test checking if task exists."""
        assert sample_config.has_task("hello")
        assert not sample_config.has_task("nonexistent")

    def test_task_names(self, sample_config):
        """Test getting sorted task names."""
        names = sample_config.task_names()
        assert names == ["build", "deploy", "hello", "test"]

    def test_parse_simple_task(self, temp_dir):
        """Test parsing simple string task."""
        config_file = temp_dir / "pyproject.toml"
        config_file.write_text(
            """
[tool.taskx.tasks]
simple = "echo 'hello'"
"""
        )
        config = Config(config_file)
        config.load()

        task = config.tasks["simple"]
        assert task.cmd == "echo 'hello'"
        assert task.description is None

    def test_parse_complex_task(self, temp_dir):
        """Test parsing complex task definition."""
        config_file = temp_dir / "pyproject.toml"
        config_file.write_text(
            """
[tool.taskx.tasks]
lint = { cmd = "ruff check .", description = "Lint code" }
complex = { cmd = "pytest", description = "Run tests", depends = ["lint"] }
"""
        )
        config = Config(config_file)
        config.load()

        task = config.tasks["complex"]
        assert task.cmd == "pytest"
        assert task.description == "Run tests"
        assert task.depends == ["lint"]

    def test_missing_config_file(self, temp_dir):
        """Test error when config file doesn't exist."""
        config = Config(temp_dir / "nonexistent.toml")
        with pytest.raises(FileNotFoundError):
            config.load()

    def test_no_taskx_section(self, temp_dir):
        """Test error when no [tool.taskx] section."""
        config_file = temp_dir / "pyproject.toml"
        config_file.write_text(
            """
[project]
name = "test"
"""
        )
        config = Config(config_file)
        with pytest.raises(ConfigError, match="No \\[tool.taskx\\] section"):
            config.load()

    def test_no_tasks_defined(self, temp_dir):
        """Test error when no tasks defined."""
        config_file = temp_dir / "pyproject.toml"
        config_file.write_text(
            """
[tool.taskx.env]
FOO = "bar"
"""
        )
        config = Config(config_file)
        with pytest.raises(ConfigError, match="No tasks defined"):
            config.load()
