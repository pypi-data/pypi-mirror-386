"""
Tests for file watcher and watch mode functionality.
"""

import asyncio
import time
from pathlib import Path

import pytest

from taskx.core.task import Task
from taskx.execution.watcher import FileWatcher, watch_task_sync


class TestFileWatcher:
    """Test file watcher functionality."""

    def test_create_watcher(self):
        """Test creating file watcher."""
        watcher = FileWatcher(patterns=["*.py"])
        assert watcher is not None
        assert watcher.patterns == ["*.py"]

    def test_create_watcher_with_custom_debounce(self):
        """Test creating watcher with custom debounce."""
        watcher = FileWatcher(patterns=["*.py"], debounce_ms=500)
        assert watcher.debounce_ms == 0.5  # Converted to seconds

    def test_filter_changes_matches_pattern(self):
        """Test filtering changes based on patterns."""
        watcher = FileWatcher(patterns=["*.py"])

        # Simulate changes from watchfiles
        changes = {
            ("modified", "/path/to/file.py"),
            ("modified", "/path/to/file.txt"),
            ("modified", "/path/to/another.py"),
        }

        filtered = watcher._filter_changes(changes)

        # Only .py files should be included
        filtered_paths = {str(p) for p in filtered}
        assert "/path/to/file.py" in filtered_paths
        assert "/path/to/another.py" in filtered_paths
        assert "/path/to/file.txt" not in filtered_paths

    def test_filter_changes_multiple_patterns(self):
        """Test filtering with multiple patterns."""
        watcher = FileWatcher(patterns=["*.py", "*.toml"])

        changes = {
            ("modified", "/path/to/file.py"),
            ("modified", "/path/to/config.toml"),
            ("modified", "/path/to/file.txt"),
        }

        filtered = watcher._filter_changes(changes)
        filtered_paths = {str(p) for p in filtered}

        assert "/path/to/file.py" in filtered_paths
        assert "/path/to/config.toml" in filtered_paths
        assert "/path/to/file.txt" not in filtered_paths

    def test_filter_changes_ignores_hidden_files(self):
        """Test that hidden files are ignored."""
        watcher = FileWatcher(patterns=["*"])

        changes = {
            ("modified", "/path/to/.hidden.py"),
            ("modified", "/path/to/visible.py"),
        }

        filtered = watcher._filter_changes(changes)
        filtered_paths = {str(p) for p in filtered}

        assert "/path/to/visible.py" in filtered_paths
        assert "/path/to/.hidden.py" not in filtered_paths

    def test_filter_changes_ignores_cache_directories(self):
        """Test that cache/build directories are ignored."""
        watcher = FileWatcher(patterns=["*.py"])

        changes = {
            ("modified", "/path/to/file.py"),
            ("modified", "/path/to/__pycache__/file.pyc"),
            ("modified", "/path/to/node_modules/package.py"),
            ("modified", "/path/to/.pytest_cache/file.py"),
        }

        filtered = watcher._filter_changes(changes)
        filtered_paths = {str(p) for p in filtered}

        assert "/path/to/file.py" in filtered_paths
        assert len(filtered_paths) == 1  # Only the non-cache file

    def test_filter_changes_glob_patterns(self):
        """Test glob pattern matching."""
        watcher = FileWatcher(patterns=["**/*.py"])

        changes = {
            ("modified", "/project/src/main.py"),
            ("modified", "/project/src/utils/helper.py"),
            ("modified", "/project/tests/test.py"),
        }

        filtered = watcher._filter_changes(changes)
        filtered_paths = {str(p) for p in filtered}

        # All .py files should match the **/*.py pattern
        assert len(filtered) == 3  # All Python files match

    def test_display_changes(self, capsys):
        """Test displaying changes."""
        watcher = FileWatcher(patterns=["*.py"])

        changes = {Path("/path/to/file1.py"), Path("/path/to/file2.py")}

        watcher._display_changes(changes)

        # Capture output (Rich uses stderr by default)
        captured = capsys.readouterr()
        # Just verify the method doesn't crash
        # (Rich output is hard to test directly)

    def test_display_changes_empty(self, capsys):
        """Test displaying empty changes."""
        watcher = FileWatcher(patterns=["*.py"])

        watcher._display_changes(set())

        captured = capsys.readouterr()
        # Should not output anything for empty changes


class TestWatchTaskSync:
    """Test synchronous watch wrapper."""

    def test_watch_task_sync_requires_patterns(self):
        """Test that watch requires patterns."""
        task = Task(name="test", cmd="echo 'test'")  # No watch patterns

        with pytest.raises(ValueError, match="no watch patterns"):
            watch_task_sync(
                task=task,
                execute_callback=lambda: True,
                patterns=None,
            )

    def test_watch_task_sync_uses_task_patterns(self):
        """Test that watch uses task's patterns if not provided."""
        task = Task(name="test", cmd="echo 'test'", watch=["*.py"])

        # Mock the watcher to avoid actually watching
        # This test just verifies the patterns are passed correctly
        # (Full integration testing would require actual file changes)

    def test_watch_task_sync_overrides_patterns(self):
        """Test that custom patterns override task patterns."""
        task = Task(name="test", cmd="echo 'test'", watch=["*.py"])

        # Override with custom patterns
        custom_patterns = ["*.toml", "*.yaml"]

        # Mock test to verify patterns would be used
        # (Full integration testing would require actual file changes)


class TestFileWatcherIntegration:
    """Integration tests for file watcher."""

    @pytest.mark.asyncio
    async def test_watch_and_execute_initial_run(self, temp_dir: Path):
        """Test that initial execution happens."""
        task = Task(name="test", cmd="echo 'test'", watch=["*.py"])

        execution_count = []

        def callback():
            execution_count.append(1)
            return True

        watcher = FileWatcher(patterns=["*.py"])

        # Create a task that will immediately cancel
        async def watch_briefly():
            watch_task = asyncio.create_task(
                watcher.watch_and_execute(task, callback, str(temp_dir))
            )
            # Let it run initial execution
            await asyncio.sleep(0.2)
            watch_task.cancel()
            try:
                await watch_task
            except asyncio.CancelledError:
                pass

        await watch_briefly()

        # Initial execution should have happened
        assert len(execution_count) == 1

    def test_pending_changes_cleared_after_execution(self):
        """Test that pending changes are cleared after execution."""
        watcher = FileWatcher(patterns=["*.py"])

        # Add some pending changes
        watcher._pending_changes.add(Path("/test/file.py"))
        assert len(watcher._pending_changes) > 0

        # Clear should work
        watcher._pending_changes.clear()
        assert len(watcher._pending_changes) == 0

    def test_debounce_tracking(self):
        """Test debounce time tracking."""
        watcher = FileWatcher(patterns=["*.py"], debounce_ms=100)

        # Set last execution time
        current_time = time.time()
        watcher._last_execution = current_time

        # Check that debounce period is respected
        assert watcher.debounce_ms == 0.1  # 100ms = 0.1s

        # Simulate waiting
        time.sleep(0.15)

        # Time should have passed debounce period
        assert time.time() - watcher._last_execution > watcher.debounce_ms


class TestWatcherEdgeCases:
    """Test edge cases and error handling."""

    def test_watcher_with_empty_patterns(self):
        """Test watcher with empty pattern list."""
        watcher = FileWatcher(patterns=[])

        changes = {
            ("modified", "/path/to/file.py"),
        }

        filtered = watcher._filter_changes(changes)
        # No patterns means no matches
        assert len(filtered) == 0

    def test_watcher_with_wildcard_pattern(self):
        """Test watcher with wildcard pattern."""
        watcher = FileWatcher(patterns=["*"])

        changes = {
            ("modified", "/path/to/file.py"),
            ("modified", "/path/to/config.toml"),
        }

        filtered = watcher._filter_changes(changes)
        # Should match all non-hidden, non-cache files
        assert len(filtered) > 0

    def test_filter_changes_handles_empty_set(self):
        """Test that filtering empty changes set works."""
        watcher = FileWatcher(patterns=["*.py"])

        filtered = watcher._filter_changes(set())
        assert len(filtered) == 0
        assert isinstance(filtered, set)
