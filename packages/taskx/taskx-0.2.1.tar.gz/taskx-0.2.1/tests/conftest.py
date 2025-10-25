"""
Pytest configuration and fixtures for taskx tests.

This module provides comprehensive fixtures for unit, integration, and performance tests.
"""

import os
import tempfile
from pathlib import Path
from typing import Any, Dict, Generator
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from taskx.core.config import Config
from taskx.core.task import Task

# ============================================================================
# Basic Fixtures
# ============================================================================


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def cli_runner() -> CliRunner:
    """Create a Click CLI test runner."""
    return CliRunner()


# ============================================================================
# Configuration Fixtures
# ============================================================================


@pytest.fixture
def basic_toml_content() -> str:
    """Basic TOML configuration content."""
    return """
[tool.taskx.env]
APP_NAME = "testapp"
VERSION = "1.0.0"

[tool.taskx.tasks]
hello = "echo 'Hello, World!'"
test = { cmd = "pytest tests/", description = "Run tests" }
build = { cmd = "python -m build", description = "Build package" }
deploy = { depends = ["test", "build"], cmd = "echo 'Deploying...'", description = "Deploy to production" }
"""


@pytest.fixture
def config_with_aliases() -> str:
    """TOML configuration with task aliases."""
    return """
[tool.taskx.env]
APP_NAME = "testapp"

[tool.taskx.aliases]
t = "test"
b = "build"
d = "deploy"
ta = "test-all"

[tool.taskx.tasks]
test = { cmd = "pytest tests/unit", description = "Run unit tests" }
test-all = { cmd = "pytest tests/", description = "Run all tests" }
build = { cmd = "python -m build", description = "Build package" }
deploy = { depends = ["test", "build"], cmd = "echo 'Deploying'", description = "Deploy" }
"""


@pytest.fixture
def config_with_prompts() -> str:
    """TOML configuration with interactive prompts."""
    return """
[tool.taskx.tasks.deploy]
cmd = "echo 'Deploying to ${ENVIRONMENT} as ${USER}'"
description = "Deploy application"
confirm = "Deploy to ${ENVIRONMENT}?"

[tool.taskx.tasks.deploy.prompt]
ENVIRONMENT = { type = "select", message = "Select environment:", choices = ["dev", "staging", "prod"], default = "dev" }
USER = { type = "text", message = "Enter username:", default = "admin" }

[tool.taskx.tasks.greet]
cmd = "echo 'Hello ${NAME}!'"

[tool.taskx.tasks.greet.prompt]
NAME = { type = "text", message = "What's your name?", default = "World" }
"""


@pytest.fixture
def sample_config_file(temp_dir: Path, basic_toml_content: str) -> Path:
    """Create a sample configuration file."""
    config_path = temp_dir / "pyproject.toml"
    config_path.write_text(basic_toml_content)
    return config_path


@pytest.fixture
def sample_config(sample_config_file: Path) -> Config:
    """Load a sample configuration."""
    config = Config(sample_config_file)
    config.load()
    return config


# ============================================================================
# Task Fixtures
# ============================================================================


@pytest.fixture
def simple_task() -> Task:
    """Create a simple task."""
    return Task(
        name="test_task",
        cmd="echo 'test'",
        description="A test task",
    )


@pytest.fixture
def task_with_dependencies() -> Task:
    """Create a task with dependencies."""
    return Task(
        name="deploy",
        cmd="echo 'Deploying...'",
        description="Deploy to production",
        depends=["test", "build"],
    )


@pytest.fixture
def task_with_aliases(temp_dir: Path, config_with_aliases: str) -> Config:
    """Create a config with task aliases."""
    config_path = temp_dir / "pyproject.toml"
    config_path.write_text(config_with_aliases)
    config = Config(config_path)
    config.load()
    return config


@pytest.fixture
def task_with_prompts(temp_dir: Path, config_with_prompts: str) -> Config:
    """Create a config with task prompts."""
    config_path = temp_dir / "pyproject.toml"
    config_path.write_text(config_with_prompts)
    config = Config(config_path)
    config.load()
    return config


# ============================================================================
# Template Fixtures
# ============================================================================


@pytest.fixture
def django_template_vars() -> Dict[str, Any]:
    """Variables for Django template testing."""
    return {
        "project_name": "myproject",
        "author": "Test Author",
        "email": "test@example.com",
        "python_version": "3.11",
    }


@pytest.fixture
def fastapi_template_vars() -> Dict[str, Any]:
    """Variables for FastAPI template testing."""
    return {
        "project_name": "myapi",
        "author": "Test Author",
        "email": "test@example.com",
        "python_version": "3.11",
    }


@pytest.fixture
def data_science_template_vars() -> Dict[str, Any]:
    """Variables for Data Science template testing."""
    return {
        "project_name": "myanalysis",
        "author": "Test Author",
        "email": "test@example.com",
        "python_version": "3.11",
    }


@pytest.fixture
def python_library_template_vars() -> Dict[str, Any]:
    """Variables for Python Library template testing."""
    return {
        "project_name": "mylib",
        "author": "Test Author",
        "email": "test@example.com",
        "python_version": "3.11",
    }


# ============================================================================
# Mock Fixtures for Interactive Testing
# ============================================================================


@pytest.fixture
def mock_stdin() -> Generator[MagicMock, None, None]:
    """Mock stdin for interactive prompt testing."""
    with patch("sys.stdin") as mock:
        mock.isatty = MagicMock(return_value=True)
        yield mock


@pytest.fixture
def mock_isatty(monkeypatch: pytest.MonkeyPatch) -> None:
    """Mock isatty to simulate interactive terminal."""
    monkeypatch.setattr("sys.stdin.isatty", lambda: True)
    monkeypatch.setattr("sys.stdout.isatty", lambda: True)


@pytest.fixture
def non_interactive_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Set up non-interactive environment (CI/CD simulation)."""
    monkeypatch.setattr("sys.stdin.isatty", lambda: False)
    monkeypatch.setenv("CI", "true")


@pytest.fixture
def interactive_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Set up interactive environment."""
    monkeypatch.setattr("sys.stdin.isatty", lambda: True)
    monkeypatch.setattr("sys.stdout.isatty", lambda: True)
    if "CI" in os.environ:
        monkeypatch.delenv("CI")


# ============================================================================
# Shell Completion Fixtures
# ============================================================================


@pytest.fixture
def bash_shell_env(monkeypatch: pytest.MonkeyPatch) -> Dict[str, str]:
    """Set up bash shell environment."""
    env = {
        "SHELL": "/bin/bash",
        "BASH_VERSION": "5.1.0",
    }
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    return env


@pytest.fixture
def zsh_shell_env(monkeypatch: pytest.MonkeyPatch) -> Dict[str, str]:
    """Set up zsh shell environment."""
    env = {
        "SHELL": "/bin/zsh",
        "ZSH_VERSION": "5.8",
    }
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    return env


@pytest.fixture
def fish_shell_env(monkeypatch: pytest.MonkeyPatch) -> Dict[str, str]:
    """Set up fish shell environment."""
    env = {
        "SHELL": "/usr/bin/fish",
        "FISH_VERSION": "3.5.0",
    }
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    return env


@pytest.fixture
def powershell_env(monkeypatch: pytest.MonkeyPatch) -> Dict[str, str]:
    """Set up PowerShell environment."""
    env = {
        "PSModulePath": "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\Modules",
    }
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    return env


# ============================================================================
# Platform Detection Fixtures
# ============================================================================


@pytest.fixture
def platform_linux(monkeypatch: pytest.MonkeyPatch) -> None:
    """Mock Linux platform."""
    monkeypatch.setattr("sys.platform", "linux")


@pytest.fixture
def platform_macos(monkeypatch: pytest.MonkeyPatch) -> None:
    """Mock macOS platform."""
    monkeypatch.setattr("sys.platform", "darwin")


@pytest.fixture
def platform_windows(monkeypatch: pytest.MonkeyPatch) -> None:
    """Mock Windows platform."""
    monkeypatch.setattr("sys.platform", "win32")


# ============================================================================
# Performance Testing Configuration
# ============================================================================


@pytest.fixture(scope="session")
def benchmark_config() -> Dict[str, Any]:
    """Configuration for pytest-benchmark."""
    return {
        "min_rounds": 5,
        "min_time": 0.000005,
        "max_time": 1.0,
        "calibration_precision": 10,
        "warmup": True,
    }


# ============================================================================
# File System Fixtures
# ============================================================================


@pytest.fixture
def project_with_tasks(temp_dir: Path) -> Path:
    """Create a complete project directory with tasks."""
    project_dir = temp_dir / "myproject"
    project_dir.mkdir()

    # Create pyproject.toml
    (project_dir / "pyproject.toml").write_text(
        """
[tool.taskx.env]
APP_NAME = "myproject"
VERSION = "1.0.0"

[tool.taskx.aliases]
t = "test"
b = "build"

[tool.taskx.tasks]
test = { cmd = "echo 'Running tests'", description = "Run tests" }
build = { cmd = "echo 'Building'", description = "Build project" }
deploy = { depends = ["test", "build"], cmd = "echo 'Deploying'", description = "Deploy" }
"""
    )

    # Create basic project structure
    (project_dir / "src").mkdir()
    (project_dir / "tests").mkdir()
    (project_dir / "src" / "__init__.py").touch()
    (project_dir / "README.md").write_text("# My Project")

    return project_dir


@pytest.fixture
def empty_project(temp_dir: Path) -> Path:
    """Create an empty project directory."""
    project_dir = temp_dir / "empty_project"
    project_dir.mkdir()
    return project_dir


# ============================================================================
# Cleanup
# ============================================================================


@pytest.fixture(autouse=True)
def cleanup_env(monkeypatch: pytest.MonkeyPatch) -> Generator[None, None, None]:
    """Clean up environment variables after each test."""
    original_env = os.environ.copy()
    yield
    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


# ============================================================================
# Test Markers Configuration
# ============================================================================


def pytest_configure(config: Any) -> None:
    """Configure custom pytest markers."""
    config.addinivalue_line("markers", "unit: marks tests as unit tests (fast, no I/O)")
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests (I/O, external deps)"
    )
    config.addinivalue_line("markers", "e2e: marks tests as end-to-end tests (full system)")
    config.addinivalue_line("markers", "performance: marks tests as performance benchmarks")
    config.addinivalue_line(
        "markers", "slow: marks tests as slow running (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line("markers", "windows: marks tests that only run on Windows")
    config.addinivalue_line("markers", "unix: marks tests that only run on Unix systems")
    config.addinivalue_line("markers", "requires_shell: marks tests that require a real shell")
