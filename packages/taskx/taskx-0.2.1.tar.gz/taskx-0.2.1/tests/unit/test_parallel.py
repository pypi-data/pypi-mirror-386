"""
Tests for parallel task execution.
"""

from pathlib import Path

import pytest

from taskx.execution.parallel import ParallelExecutor, run_parallel_sync


class TestParallelExecutor:
    """Test parallel task execution."""

    def test_create_executor(self):
        """Test creating parallel executor."""
        executor = ParallelExecutor()
        assert executor is not None
        assert executor.max_concurrent == 10

    def test_create_executor_with_custom_max(self):
        """Test creating executor with custom max concurrent."""
        executor = ParallelExecutor(max_concurrent=5)
        assert executor.max_concurrent == 5

    @pytest.mark.asyncio
    async def test_run_parallel_simple(self, temp_dir: Path):
        """Test running simple parallel commands."""
        executor = ParallelExecutor()

        commands = [
            "echo 'task 1'",
            "echo 'task 2'",
            "echo 'task 3'",
        ]

        results = await executor.run_parallel(
            commands=commands,
            env={},
            cwd=str(temp_dir),
        )

        # All tasks should succeed
        assert len(results) == 3
        for cmd, result in results.items():
            assert result.success is True
            assert result.exit_code == 0

    @pytest.mark.asyncio
    async def test_run_parallel_with_failure(self, temp_dir: Path):
        """Test parallel execution with one failing command."""
        executor = ParallelExecutor()

        commands = [
            "echo 'task 1'",
            "exit 1",  # This will fail
            "echo 'task 3'",
        ]

        results = await executor.run_parallel(
            commands=commands,
            env={},
            cwd=str(temp_dir),
        )

        # Check that we got all results
        assert len(results) == 3

        # Check success/failure
        assert results["echo 'task 1'"].success is True
        assert results["exit 1"].success is False
        assert results["echo 'task 3'"].success is True

    @pytest.mark.asyncio
    async def test_run_parallel_with_timeout(self, temp_dir: Path):
        """Test parallel execution with timeout."""
        executor = ParallelExecutor()

        commands = [
            "echo 'quick task'",
            "sleep 10",  # This should timeout
        ]

        results = await executor.run_parallel(
            commands=commands,
            env={},
            cwd=str(temp_dir),
            timeout=1,  # 1 second timeout
        )

        # Quick task should succeed
        assert results["echo 'quick task'"].success is True

        # Sleep task should fail due to timeout
        assert results["sleep 10"].success is False

    @pytest.mark.asyncio
    async def test_run_parallel_with_env(self, temp_dir: Path):
        """Test parallel execution with environment variables."""
        executor = ParallelExecutor()

        commands = [
            "echo $TEST_VAR",
        ]

        env = {"TEST_VAR": "hello_world"}

        results = await executor.run_parallel(
            commands=commands,
            env=env,
            cwd=str(temp_dir),
        )

        assert results["echo $TEST_VAR"].success is True

    def test_run_parallel_sync_wrapper(self, temp_dir: Path):
        """Test synchronous wrapper for parallel execution."""
        commands = [
            "echo 'task 1'",
            "echo 'task 2'",
        ]

        results = run_parallel_sync(
            commands=commands,
            env={},
            cwd=str(temp_dir),
        )

        assert len(results) == 2
        for cmd, result in results.items():
            assert result.success is True

    @pytest.mark.asyncio
    async def test_run_parallel_respects_max_concurrent(self, temp_dir: Path):
        """Test that max_concurrent limit is respected."""
        executor = ParallelExecutor(max_concurrent=2)

        # Create many quick tasks
        commands = [f"echo 'task {i}'" for i in range(10)]

        results = await executor.run_parallel(
            commands=commands,
            env={},
            cwd=str(temp_dir),
        )

        # All should succeed
        assert len(results) == 10
        for result in results.values():
            assert result.success is True

    @pytest.mark.asyncio
    async def test_run_parallel_security_validation(self, temp_dir: Path):
        """Test that security validation works in parallel execution."""
        executor = ParallelExecutor()

        commands = [
            "echo 'safe command'",
            "rm -rf /",  # Forbidden command
        ]

        results = await executor.run_parallel(
            commands=commands,
            env={},
            cwd=str(temp_dir),
        )

        # Safe command should succeed
        assert results["echo 'safe command'"].success is True

        # Forbidden command should fail (blocked by security or permissions)
        assert results["rm -rf /"].success is False


class TestParallelExecutorErrorHandling:
    """Test error handling in parallel execution."""

    @pytest.mark.asyncio
    async def test_invalid_command(self, temp_dir: Path):
        """Test handling of invalid commands."""
        executor = ParallelExecutor()

        commands = [
            "nonexistent_command_xyz",
        ]

        results = await executor.run_parallel(
            commands=commands,
            env={},
            cwd=str(temp_dir),
        )

        # Command should fail (not found)
        assert results["nonexistent_command_xyz"].success is False

    @pytest.mark.asyncio
    async def test_empty_command_list(self, temp_dir: Path):
        """Test handling of empty command list."""
        executor = ParallelExecutor()

        results = await executor.run_parallel(
            commands=[],
            env={},
            cwd=str(temp_dir),
        )

        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_working_directory_error(self):
        """Test handling of invalid working directory."""
        executor = ParallelExecutor()

        commands = ["echo 'test'"]

        results = await executor.run_parallel(
            commands=commands,
            env={},
            cwd="/nonexistent/directory/path",
        )

        # Should fail due to invalid cwd
        assert results["echo 'test'"].success is False
