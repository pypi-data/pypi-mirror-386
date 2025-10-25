"""Tests for task module."""

import pytest

from taskx.core.task import ExecutionResult, Hook, Task


class TestTask:
    """Test Task model."""

    def test_create_simple_task(self):
        """Test creating a simple task."""
        task = Task(name="test", cmd="echo 'hello'")
        assert task.name == "test"
        assert task.cmd == "echo 'hello'"
        assert task.description is None
        assert task.depends == []

    def test_create_task_with_dependencies(self):
        """Test creating task with dependencies."""
        task = Task(
            name="deploy",
            cmd="deploy.sh",
            depends=["test", "build"],
        )
        assert task.depends == ["test", "build"]
        assert task.has_dependencies

    def test_task_validation_no_name(self):
        """Test that task name is required."""
        with pytest.raises(ValueError, match="name cannot be empty"):
            Task(name="", cmd="echo 'test'")

    def test_task_validation_no_command(self):
        """Test that either cmd or parallel is required."""
        with pytest.raises(ValueError, match="must have either"):
            Task(name="test")

    def test_task_is_parallel(self):
        """Test parallel task detection."""
        task = Task(name="parallel", parallel=["cmd1", "cmd2"])
        assert task.is_parallel
        assert not task.cmd

    def test_task_has_hooks(self):
        """Test hook detection."""
        task = Task(name="test", cmd="echo 'test'", pre="echo 'before'")
        assert task.has_hooks


class TestExecutionResult:
    """Test ExecutionResult model."""

    def test_create_result(self):
        """Test creating execution result."""
        result = ExecutionResult(
            task_name="test",
            success=True,
            exit_code=0,
            duration=1.5,
        )
        assert result.task_name == "test"
        assert result.success
        assert result.exit_code == 0
        assert result.duration == 1.5
        assert not result.failed

    def test_failed_result(self):
        """Test failed result."""
        result = ExecutionResult(
            task_name="test",
            success=False,
            exit_code=1,
        )
        assert result.failed
        assert not result.success


class TestHook:
    """Test Hook model."""

    def test_create_hook(self):
        """Test creating a hook."""
        hook = Hook(name="pre", cmd="echo 'before'", task_name="test")
        assert hook.name == "pre"
        assert hook.cmd == "echo 'before'"
        assert hook.task_name == "test"

    def test_invalid_hook_name(self):
        """Test that hook name must be valid."""
        with pytest.raises(ValueError, match="Invalid hook name"):
            Hook(name="invalid", cmd="echo 'test'", task_name="test")
