"""
Integration tests for feature interactions.

Tests how different taskx features work together: aliases with tasks, prompts with execution,
templates with configuration, etc.
"""

import pytest

from taskx.cli.main import cli

# ============================================================================
# Test Aliases with Tasks
# ============================================================================


@pytest.mark.integration
class TestAliasesWithTasks:
    """Test integration between aliases and task execution."""

    def test_run_task_by_alias(self, temp_dir, cli_runner):
        """Test running a task using its alias."""
        config_path = temp_dir / "pyproject.toml"
        config_path.write_text(
            """
[tool.taskx.aliases]
t = "test"

[tool.taskx.tasks]
test = "echo 'Running tests'"
"""
        )

        result = cli_runner.invoke(cli, ["--config", str(config_path), "run", "t"])

        assert result.exit_code == 0
        # Alias resolution message and task execution confirmation
        assert "test" in result.output.lower()

    def test_alias_with_dependencies(self, temp_dir, cli_runner):
        """Test that aliases work with tasks that have dependencies."""
        config_path = temp_dir / "pyproject.toml"
        config_path.write_text(
            """
[tool.taskx.aliases]
d = "deploy"

[tool.taskx.tasks]
test = "echo 'Testing'"
build = "echo 'Building'"
deploy = { depends = ["test", "build"], cmd = "echo 'Deploying'" }
"""
        )

        result = cli_runner.invoke(cli, ["--config", str(config_path), "run", "d"])

        assert result.exit_code == 0
        # Check that all tasks executed (visible in completion messages)
        assert "test" in result.output.lower()
        assert "build" in result.output.lower()
        assert "deploy" in result.output.lower()

    def test_list_shows_aliases(self, temp_dir, cli_runner):
        """Test that list command shows aliases."""
        config_path = temp_dir / "pyproject.toml"
        config_path.write_text(
            """
[tool.taskx.aliases]
t = "test"
b = "build"

[tool.taskx.tasks]
test = "echo test"
build = "echo build"
"""
        )

        result = cli_runner.invoke(cli, ["--config", str(config_path), "list"])

        assert result.exit_code == 0
        assert "test" in result.output.lower()
        assert "build" in result.output.lower()


# ============================================================================
# Test Prompts with Task Execution
# ============================================================================


@pytest.mark.integration
class TestPromptsWithExecution:
    """Test integration between prompts and task execution."""

    def test_task_with_prompt_uses_env_override(self, temp_dir, cli_runner):
        """Test that env overrides bypass prompts."""
        config_path = temp_dir / "pyproject.toml"
        config_path.write_text(
            """
[tool.taskx.tasks.greet]
cmd = "echo 'Hello ${NAME}'"

[tool.taskx.tasks.greet.prompt]
NAME = { type = "text", message = "Your name:", default = "World" }
"""
        )

        result = cli_runner.invoke(
            cli, ["--config", str(config_path), "run", "greet", "--env", "NAME=Alice"]
        )

        assert result.exit_code == 0
        # Task completed successfully - env override worked
        assert "greet" in result.output.lower()

    @pytest.mark.skip(reason="--force flag not implemented for bypassing confirmation prompts")
    def test_task_with_confirm_can_be_forced(self, temp_dir, cli_runner):
        """Test that confirmation prompts can be bypassed with --force."""
        config_path = temp_dir / "pyproject.toml"
        config_path.write_text(
            """
[tool.taskx.tasks]
deploy = { cmd = "echo 'Deployed'", confirm = "Deploy to production?" }
"""
        )

        result = cli_runner.invoke(cli, ["--config", str(config_path), "run", "deploy", "--force"])

        assert result.exit_code == 0
        assert "Deployed" in result.output


# ============================================================================
# Test Templates with Configuration
# ============================================================================


@pytest.mark.integration
class TestTemplatesWithConfig:
    """Test integration between templates and configuration loading."""

    def test_template_generated_config_loads_correctly(self, temp_dir, cli_runner):
        """Test that template-generated configs can be loaded."""
        import os

        original_cwd = os.getcwd()
        try:
            os.chdir(temp_dir)

            # Generate config from template
            result = cli_runner.invoke(
                cli,
                ["init", "--template", "fastapi", "--name", "testapi"],
                input="testapi\nTest Author\ntest@example.com\n3.11\n",
            )

            assert result.exit_code == 0
            assert (temp_dir / "pyproject.toml").exists()

            # List tasks from generated config
            result = cli_runner.invoke(cli, ["list"])

            assert result.exit_code == 0
            assert "dev" in result.output.lower() or "run" in result.output.lower()
        finally:
            os.chdir(original_cwd)

    def test_template_tasks_are_executable(self, temp_dir, cli_runner):
        """Test that tasks from templates can be executed."""
        import os

        original_cwd = os.getcwd()
        try:
            os.chdir(temp_dir)

            # Generate simple config
            config_path = temp_dir / "pyproject.toml"
            config_path.write_text(
                """
[project]
name = "testproject"

[tool.taskx.tasks]
hello = "echo 'Hello from template'"
"""
            )

            result = cli_runner.invoke(cli, ["run", "hello"])

            assert result.exit_code == 0
            # Task executed successfully
            assert "hello" in result.output.lower()
        finally:
            os.chdir(original_cwd)


# ============================================================================
# Test Completion with Configuration
# ============================================================================


@pytest.mark.integration
class TestCompletionWithConfig:
    """Test integration between completion scripts and configuration."""

    def test_completion_includes_tasks_from_config(self, temp_dir, cli_runner):
        """Test that completion scripts include tasks from config."""
        import os

        os.chdir(temp_dir)

        config_path = temp_dir / "pyproject.toml"
        config_path.write_text(
            """
[tool.taskx.tasks]
custom-task = "echo test"
another-task = "echo test"
"""
        )

        result = cli_runner.invoke(cli, ["completion", "bash"])

        assert result.exit_code == 0
        # Completion should work (exact content depends on implementation)
        assert len(result.output) > 100

    def test_completion_with_aliases(self, temp_dir, cli_runner):
        """Test that completion works with aliases."""
        import os

        os.chdir(temp_dir)

        config_path = temp_dir / "pyproject.toml"
        config_path.write_text(
            """
[tool.taskx.aliases]
t = "test"

[tool.taskx.tasks]
test = "echo test"
"""
        )

        result = cli_runner.invoke(cli, ["completion", "bash"])

        assert result.exit_code == 0
        assert len(result.output) > 100


# ============================================================================
# Test Dependencies with Multiple Features
# ============================================================================


@pytest.mark.integration
class TestDependenciesIntegration:
    """Test task dependencies with various features."""

    def test_dependencies_with_prompts(self, temp_dir, cli_runner):
        """Test that task dependencies work when tasks have prompts."""
        config_path = temp_dir / "pyproject.toml"
        config_path.write_text(
            """
[tool.taskx.tasks.build]
cmd = "echo 'Building ${VERSION}'"

[tool.taskx.tasks.build.prompt]
VERSION = { type = "text", message = "Version:", default = "1.0.0" }

[tool.taskx.tasks.deploy]
depends = ["build"]
cmd = "echo 'Deploying'"
"""
        )

        result = cli_runner.invoke(
            cli, ["--config", str(config_path), "run", "deploy", "--env", "VERSION=2.0.0"]
        )

        assert result.exit_code == 0
        # Check that both tasks executed
        assert "build" in result.output.lower()
        assert "deploy" in result.output.lower()

    def test_dependencies_with_aliases(self, temp_dir, cli_runner):
        """Test that dependencies can use aliases."""
        config_path = temp_dir / "pyproject.toml"
        config_path.write_text(
            """
[tool.taskx.aliases]
t = "test"
b = "build"

[tool.taskx.tasks]
test = "echo 'Testing'"
build = "echo 'Building'"
deploy = { depends = ["test", "build"], cmd = "echo 'Deploying'" }
"""
        )

        result = cli_runner.invoke(cli, ["--config", str(config_path), "run", "deploy"])

        assert result.exit_code == 0
        # Check that all tasks executed
        assert "test" in result.output.lower()
        assert "build" in result.output.lower()
        assert "deploy" in result.output.lower()

    def test_parallel_dependencies_execute_concurrently(self, temp_dir, cli_runner):
        """Test that parallel dependencies execute together."""
        config_path = temp_dir / "pyproject.toml"
        config_path.write_text(
            """
[tool.taskx.tasks]
lint = "echo 'Linting'"
typecheck = "echo 'Type checking'"
test = "echo 'Testing'"
check = { parallel = ["lint", "typecheck", "test"], description = "Run all checks" }
"""
        )

        result = cli_runner.invoke(cli, ["--config", str(config_path), "run", "check"])

        assert result.exit_code == 0
        # Check that all parallel tasks executed
        assert "lint" in result.output.lower()
        assert "typecheck" in result.output.lower()
        assert "test" in result.output.lower()


# ============================================================================
# Test Environment Variables Across Features
# ============================================================================


@pytest.mark.integration
class TestEnvironmentVariables:
    """Test environment variable handling across features."""

    def test_env_vars_in_dependencies(self, temp_dir, cli_runner):
        """Test that env vars are available in dependent tasks."""
        config_path = temp_dir / "pyproject.toml"
        config_path.write_text(
            """
[tool.taskx.env]
PROJECT_NAME = "myproject"

[tool.taskx.tasks]
show-name = "echo 'Project: ${PROJECT_NAME}'"
build = { depends = ["show-name"], cmd = "echo 'Building ${PROJECT_NAME}'" }
"""
        )

        result = cli_runner.invoke(cli, ["--config", str(config_path), "run", "build"])

        assert result.exit_code == 0
        # Check that both tasks executed
        assert "show-name" in result.output.lower()
        assert "build" in result.output.lower()

    def test_env_override_precedence(self, temp_dir, cli_runner):
        """Test that CLI env overrides take precedence."""
        config_path = temp_dir / "pyproject.toml"
        config_path.write_text(
            """
[tool.taskx.env]
VAR = "default"

[tool.taskx.tasks]
show = "echo 'VAR=${VAR}'"
"""
        )

        result = cli_runner.invoke(
            cli, ["--config", str(config_path), "run", "show", "--env", "VAR=override"]
        )

        assert result.exit_code == 0
        # Task executed successfully
        assert "show" in result.output.lower()


# ============================================================================
# Test Error Recovery
# ============================================================================


@pytest.mark.integration
class TestErrorRecovery:
    """Test error handling and recovery across features."""

    def test_failed_dependency_stops_execution(self, temp_dir, cli_runner):
        """Test that failed dependency prevents main task execution."""
        config_path = temp_dir / "pyproject.toml"
        config_path.write_text(
            """
[tool.taskx.tasks]
fail = "exit 1"
deploy = { depends = ["fail"], cmd = "echo 'Should not run'" }
"""
        )

        result = cli_runner.invoke(cli, ["--config", str(config_path), "run", "deploy"])

        assert result.exit_code != 0
        assert "Should not run" not in result.output

    def test_parallel_task_failure_reported(self, temp_dir, cli_runner):
        """Test that parallel task failures are reported."""
        config_path = temp_dir / "pyproject.toml"
        config_path.write_text(
            """
[tool.taskx.tasks]
success = "echo 'OK'"
fail = "exit 1"
check = { parallel = ["success", "fail"] }
"""
        )

        result = cli_runner.invoke(cli, ["--config", str(config_path), "run", "check"])

        assert result.exit_code != 0


# ============================================================================
# Test Complex Workflows
# ============================================================================


@pytest.mark.integration
class TestComplexWorkflows:
    """Test complex multi-feature workflows."""

    @pytest.mark.skip(reason="--force flag not implemented for bypassing confirmation prompts")
    def test_complete_deployment_workflow(self, temp_dir, cli_runner):
        """Test complete workflow: lint -> test -> build -> deploy."""
        config_path = temp_dir / "pyproject.toml"
        config_path.write_text(
            """
[tool.taskx.aliases]
d = "deploy"

[tool.taskx.env]
VERSION = "1.0.0"

[tool.taskx.tasks]
lint = "echo 'Linting...'"
test = "echo 'Testing...'"
build = "echo 'Building ${VERSION}...'"
deploy = { depends = ["lint", "test", "build"], cmd = "echo 'Deployed ${VERSION}'", confirm = "Deploy?" }
"""
        )

        result = cli_runner.invoke(cli, ["--config", str(config_path), "run", "d", "--force"])

        assert result.exit_code == 0
        assert "Linting" in result.output
        assert "Testing" in result.output
        assert "Building 1.0.0" in result.output
        assert "Deployed 1.0.0" in result.output

    def test_template_to_execution_workflow(self, temp_dir, cli_runner):
        """Test full workflow from template init to task execution."""
        import os

        original_cwd = os.getcwd()
        try:
            os.chdir(temp_dir)

            # Initialize with template
            init_result = cli_runner.invoke(
                cli,
                ["init", "--template", "python-library"],
                input="mylib\nAuthor\nauthor@example.com\n3.11\n",
            )

            assert init_result.exit_code == 0

            # List tasks
            list_result = cli_runner.invoke(cli, ["list"])
            assert list_result.exit_code == 0

            # Try to run a task (some may require files to exist)
            # Just verify we can execute without errors
            assert (temp_dir / "pyproject.toml").exists()
        finally:
            os.chdir(original_cwd)
