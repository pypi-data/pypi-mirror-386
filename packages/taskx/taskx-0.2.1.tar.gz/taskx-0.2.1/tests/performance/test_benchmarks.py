"""
Performance benchmarks for taskx.

Tests the performance of critical operations using pytest-benchmark.
"""

import pytest

from taskx.completion.bash import BashCompletion
from taskx.core.config import Config
from taskx.core.runner import TaskRunner
from taskx.templates import get_template

# ============================================================================
# Configuration Loading Benchmarks
# ============================================================================


@pytest.mark.performance
class TestConfigLoadingPerformance:
    """Benchmark configuration loading performance."""

    def test_benchmark_load_simple_config(self, benchmark, temp_dir):
        """Benchmark loading a simple configuration."""
        config_path = temp_dir / "pyproject.toml"
        config_path.write_text(
            """
[tool.taskx.tasks]
test = "echo test"
build = "echo build"
deploy = "echo deploy"
"""
        )

        def load_config():
            config = Config(config_path)
            config.load()
            return config

        result = benchmark(load_config)
        assert result is not None

    def test_benchmark_load_config_with_many_tasks(self, benchmark, temp_dir):
        """Benchmark loading configuration with many tasks."""
        config_path = temp_dir / "pyproject.toml"
        tasks = "\n".join([f'task{i} = "echo task{i}"' for i in range(100)])
        config_path.write_text(
            f"""
[tool.taskx.tasks]
{tasks}
"""
        )

        def load_config():
            config = Config(config_path)
            config.load()
            return config

        result = benchmark(load_config)
        assert len(result.tasks) == 100

    def test_benchmark_load_config_with_aliases(self, benchmark, temp_dir):
        """Benchmark loading configuration with aliases."""
        config_path = temp_dir / "pyproject.toml"
        aliases = "\n".join([f'alias{i} = "task{i}"' for i in range(50)])
        tasks = "\n".join([f'task{i} = "echo task{i}"' for i in range(50)])
        config_path.write_text(
            f"""
[tool.taskx.aliases]
{aliases}

[tool.taskx.tasks]
{tasks}
"""
        )

        def load_config():
            config = Config(config_path)
            config.load()
            return config

        result = benchmark(load_config)
        assert len(result.aliases) == 50


# ============================================================================
# Task Execution Benchmarks
# ============================================================================


@pytest.mark.performance
class TestTaskExecutionPerformance:
    """Benchmark task execution performance."""

    def test_benchmark_simple_task_execution(self, benchmark, temp_dir):
        """Benchmark executing a simple task."""
        config_path = temp_dir / "pyproject.toml"
        config_path.write_text(
            """
[tool.taskx.tasks]
test = "echo 'benchmark test'"
"""
        )

        config = Config(config_path)
        config.load()

        runner = TaskRunner(config)

        def run_task():
            return runner.run("test")

        benchmark(run_task)

    def test_benchmark_task_with_dependencies(self, benchmark, temp_dir):
        """Benchmark executing task with dependencies."""
        config_path = temp_dir / "pyproject.toml"
        config_path.write_text(
            """
[tool.taskx.tasks]
dep1 = "echo 'dep1'"
dep2 = "echo 'dep2'"
dep3 = "echo 'dep3'"
main = { depends = ["dep1", "dep2", "dep3"], cmd = "echo 'main'" }
"""
        )

        config = Config(config_path)
        config.load()

        runner = TaskRunner(config)

        def run_task():
            return runner.run("main")

        benchmark(run_task)

    def test_benchmark_dependency_resolution(self, benchmark, temp_dir):
        """Benchmark dependency resolution performance."""
        config_path = temp_dir / "pyproject.toml"
        # Create deep dependency chain
        config_path.write_text(
            """
[tool.taskx.tasks]
task0 = "echo 'task0'"
task1 = { depends = ["task0"], cmd = "echo 'task1'" }
task2 = { depends = ["task1"], cmd = "echo 'task2'" }
task3 = { depends = ["task2"], cmd = "echo 'task3'" }
task4 = { depends = ["task3"], cmd = "echo 'task4'" }
task5 = { depends = ["task4"], cmd = "echo 'task5'" }
"""
        )

        config = Config(config_path)
        config.load()

        runner = TaskRunner(config)

        def resolve_deps():
            return runner.dependency_resolver.resolve_dependencies("task5")

        benchmark(resolve_deps)


# ============================================================================
# Template Generation Benchmarks
# ============================================================================


@pytest.mark.performance
class TestTemplatePerformance:
    """Benchmark template generation performance."""

    @pytest.mark.parametrize(
        "template_name", ["django", "fastapi", "data-science", "python-library"]
    )
    def test_benchmark_template_generation(self, benchmark, template_name):
        """Benchmark template content generation."""
        template = get_template(template_name)
        variables = {
            "project_name": "benchmark_project",
            "author": "Benchmark Author",
            "email": "bench@example.com",
            "python_version": "3.11",
        }

        def generate():
            return template.generate(variables)

        result = benchmark(generate)
        assert len(result) > 0

    def test_benchmark_template_prompts(self, benchmark):
        """Benchmark getting template prompts."""
        template = get_template("fastapi")

        def get_prompts():
            return template.get_prompts()

        result = benchmark(get_prompts)
        assert len(result) > 0


# ============================================================================
# Completion Generation Benchmarks
# ============================================================================


@pytest.mark.performance
class TestCompletionPerformance:
    """Benchmark completion script generation performance."""

    def test_benchmark_bash_completion_generation(self, benchmark, temp_dir):
        """Benchmark Bash completion generation."""
        config_path = temp_dir / "pyproject.toml"
        tasks = "\n".join([f'task{i} = "echo task{i}"' for i in range(50)])
        config_path.write_text(
            f"""
[tool.taskx.tasks]
{tasks}
"""
        )

        config = Config(config_path)
        config.load()

        generator = BashCompletion(config)

        def generate():
            return generator.generate()

        result = benchmark(generate)
        assert len(result) > 100

    def test_benchmark_completion_with_many_tasks(self, benchmark, temp_dir):
        """Benchmark completion generation with many tasks."""
        config_path = temp_dir / "pyproject.toml"
        tasks = "\n".join([f'task{i} = "echo task{i}"' for i in range(200)])
        config_path.write_text(
            f"""
[tool.taskx.tasks]
{tasks}
"""
        )

        config = Config(config_path)
        config.load()

        generator = BashCompletion(config)

        def generate():
            return generator.generate()

        result = benchmark(generate)
        assert len(result) > 100


# ============================================================================
# Alias Resolution Benchmarks
# ============================================================================


@pytest.mark.performance
class TestAliasPerformance:
    """Benchmark alias resolution performance."""

    def test_benchmark_alias_resolution(self, benchmark, temp_dir):
        """Benchmark alias resolution performance."""
        config_path = temp_dir / "pyproject.toml"
        aliases = "\n".join([f'alias{i} = "task{i}"' for i in range(100)])
        tasks = "\n".join([f'task{i} = "echo task{i}"' for i in range(100)])
        config_path.write_text(
            f"""
[tool.taskx.aliases]
{aliases}

[tool.taskx.tasks]
{tasks}
"""
        )

        config = Config(config_path)
        config.load()

        def resolve_alias():
            return config.aliases.get("alias50")

        result = benchmark(resolve_alias)
        assert result == "task50"


# ============================================================================
# Scalability Benchmarks
# ============================================================================


@pytest.mark.performance
class TestScalabilityBenchmarks:
    """Test performance at scale."""

    @pytest.mark.parametrize("task_count", [10, 50, 100, 200])
    def test_benchmark_config_load_scale(self, benchmark, temp_dir, task_count):
        """Benchmark config loading with varying task counts."""
        config_path = temp_dir / "pyproject.toml"
        tasks = "\n".join([f'task{i} = "echo task{i}"' for i in range(task_count)])
        config_path.write_text(
            f"""
[tool.taskx.tasks]
{tasks}
"""
        )

        def load_config():
            config = Config(config_path)
            config.load()
            return config

        result = benchmark(load_config)
        assert len(result.tasks) == task_count

    @pytest.mark.parametrize("depth", [1, 3, 5, 10])
    def test_benchmark_dependency_depth_scale(self, benchmark, temp_dir, depth):
        """Benchmark dependency resolution with varying depths."""
        config_path = temp_dir / "pyproject.toml"

        # Create dependency chain of specified depth
        tasks = ['task0 = "echo task0"']
        for i in range(1, depth + 1):
            tasks.append(f'task{i} = {{ depends = ["task{i-1}"], cmd = "echo task{i}" }}')

        config_path.write_text(
            f"""
[tool.taskx.tasks]
{chr(10).join(tasks)}
"""
        )

        config = Config(config_path)
        config.load()

        runner = TaskRunner(config)

        def resolve_deps():
            return runner.dependency_resolver.resolve_dependencies(f"task{depth}")

        benchmark(resolve_deps)


# ============================================================================
# Memory Efficiency Benchmarks
# ============================================================================


@pytest.mark.performance
class TestMemoryEfficiency:
    """Test memory efficiency of operations."""

    def test_benchmark_large_config_memory(self, benchmark, temp_dir):
        """Benchmark memory usage with large configuration."""
        config_path = temp_dir / "pyproject.toml"

        # Create large config
        tasks = []
        for i in range(500):
            desc = f"Task {i} that does something important " * 10  # Long description
            tasks.append(f'task{i} = {{ cmd = "echo task{i}", description = "{desc}" }}')

        config_path.write_text(
            f"""
[tool.taskx.tasks]
{chr(10).join(tasks)}
"""
        )

        def load_large_config():
            config = Config(config_path)
            config.load()
            return config

        result = benchmark(load_large_config)
        assert len(result.tasks) == 500

    def test_benchmark_multiple_config_loads(self, benchmark, temp_dir):
        """Benchmark loading config multiple times."""
        config_path = temp_dir / "pyproject.toml"
        config_path.write_text(
            """
[tool.taskx.tasks]
test = "echo test"
build = "echo build"
"""
        )

        def load_10_times():
            for _ in range(10):
                config = Config(config_path)
                config.load()
            return config

        benchmark(load_10_times)


# ============================================================================
# CLI Performance Benchmarks
# ============================================================================


@pytest.mark.performance
class TestCLIPerformance:
    """Benchmark CLI operations."""

    def test_benchmark_cli_startup(self, benchmark, temp_dir, cli_runner):
        """Benchmark CLI startup time."""
        from taskx.cli.main import cli

        config_path = temp_dir / "pyproject.toml"
        config_path.write_text(
            """
[tool.taskx.tasks]
test = "echo test"
"""
        )

        def invoke_list():
            result = cli_runner.invoke(cli, ["--config", str(config_path), "list"])
            return result

        result = benchmark(invoke_list)
        assert result.exit_code == 0

    def test_benchmark_task_lookup(self, benchmark, temp_dir):
        """Benchmark task lookup performance."""
        config_path = temp_dir / "pyproject.toml"
        tasks = "\n".join([f'task{i} = "echo task{i}"' for i in range(100)])
        config_path.write_text(
            f"""
[tool.taskx.tasks]
{tasks}
"""
        )

        config = Config(config_path)
        config.load()

        def lookup_task():
            return config.tasks.get("task50")

        result = benchmark(lookup_task)
        assert result is not None


# ============================================================================
# Performance Regression Tests
# ============================================================================


@pytest.mark.performance
class TestPerformanceRegression:
    """Test for performance regressions."""

    def test_config_load_within_threshold(self, benchmark, temp_dir):
        """Ensure config loading stays within performance threshold."""
        config_path = temp_dir / "pyproject.toml"
        tasks = "\n".join([f'task{i} = "echo task{i}"' for i in range(100)])
        config_path.write_text(
            f"""
[tool.taskx.tasks]
{tasks}
"""
        )

        def load_config():
            config = Config(config_path)
            config.load()
            return config

        result = benchmark(load_config)

        # Assert performance threshold (should complete in < 100ms)
        assert benchmark.stats.stats.mean < 0.1

    def test_task_execution_overhead(self, benchmark, temp_dir):
        """Test task execution overhead is minimal."""
        config_path = temp_dir / "pyproject.toml"
        config_path.write_text(
            """
[tool.taskx.tasks]
noop = "true"  # Minimal command
"""
        )

        config = Config(config_path)
        config.load()

        runner = TaskRunner(config)

        def run_noop():
            return runner.run("noop")

        benchmark(run_noop)

        # Overhead should be minimal (< 50ms)
        assert benchmark.stats.stats.mean < 0.05
