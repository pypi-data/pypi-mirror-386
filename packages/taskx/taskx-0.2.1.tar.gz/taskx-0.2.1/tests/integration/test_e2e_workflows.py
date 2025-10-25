"""
End-to-end workflow tests.

Tests complete user workflows from start to finish.
"""

import os

import pytest

from taskx.cli.main import cli

# ============================================================================
# Test Project Initialization Workflows
# ============================================================================


@pytest.mark.integration
@pytest.mark.e2e
class TestInitializationWorkflows:
    """Test complete project initialization workflows."""

    def test_init_basic_project(self, temp_dir, cli_runner):
        """Test initializing a basic project."""
        os.chdir(temp_dir)

        # Initialize project
        result = cli_runner.invoke(cli, ["init", "--name", "myproject"])

        assert result.exit_code == 0
        assert (temp_dir / "pyproject.toml").exists()
        assert "Success" in result.output

        # Verify we can list tasks
        result = cli_runner.invoke(cli, ["list"])
        assert result.exit_code == 0

    def test_init_with_template_complete_flow(self, temp_dir, cli_runner):
        """Test complete template initialization flow."""
        os.chdir(temp_dir)

        # List available templates
        result = cli_runner.invoke(cli, ["init", "--list-templates"])
        assert result.exit_code == 0
        assert "django" in result.output.lower()
        assert "fastapi" in result.output.lower()

        # Initialize with template
        result = cli_runner.invoke(
            cli,
            ["init", "--template", "fastapi"],
            input="myapi\nTest Author\ntest@example.com\n3.11\n",
        )

        assert result.exit_code == 0
        assert (temp_dir / "pyproject.toml").exists()
        assert (temp_dir / "README.md").exists()
        assert (temp_dir / ".gitignore").exists()

        # List generated tasks
        result = cli_runner.invoke(cli, ["list"])
        assert result.exit_code == 0
        assert "dev" in result.output.lower() or "test" in result.output.lower()

    def test_init_refuses_overwrite_without_confirm(self, temp_dir, cli_runner):
        """Test that init refuses to overwrite existing config without confirmation."""
        os.chdir(temp_dir)

        # Create initial config
        cli_runner.invoke(cli, ["init", "--name", "project1"])

        # Try to overwrite without confirming
        result = cli_runner.invoke(cli, ["init", "--name", "project2"], input="n\n")

        assert result.exit_code == 0
        assert "cancelled" in result.output.lower() or "overwrite" in result.output.lower()

        # Verify original config is unchanged
        config = (temp_dir / "pyproject.toml").read_text()
        assert "project1" in config


# ============================================================================
# Test Task Execution Workflows
# ============================================================================


@pytest.mark.integration
@pytest.mark.e2e
class TestExecutionWorkflows:
    """Test complete task execution workflows."""

    def test_simple_task_execution(self, temp_dir, cli_runner):
        """Test executing a simple task."""
        os.chdir(temp_dir)

        config = temp_dir / "pyproject.toml"
        config.write_text(
            """
[tool.taskx.tasks]
greet = "echo 'Hello, World!'"
"""
        )

        result = cli_runner.invoke(cli, ["run", "greet"])

        assert result.exit_code == 0
        assert "Hello, World!" in result.output

    def test_dependency_chain_execution(self, temp_dir, cli_runner):
        """Test executing tasks with dependency chain."""
        os.chdir(temp_dir)

        config = temp_dir / "pyproject.toml"
        config.write_text(
            """
[tool.taskx.tasks]
clean = "echo 'Cleaning...'"
lint = { depends = ["clean"], cmd = "echo 'Linting...'" }
test = { depends = ["lint"], cmd = "echo 'Testing...'" }
build = { depends = ["test"], cmd = "echo 'Building...'" }
"""
        )

        result = cli_runner.invoke(cli, ["run", "build"])

        assert result.exit_code == 0
        # All tasks in chain should execute
        assert "Cleaning" in result.output
        assert "Linting" in result.output
        assert "Testing" in result.output
        assert "Building" in result.output

        # Verify execution order
        clean_pos = result.output.find("Cleaning")
        lint_pos = result.output.find("Linting")
        test_pos = result.output.find("Testing")
        build_pos = result.output.find("Building")

        assert clean_pos < lint_pos < test_pos < build_pos

    def test_parallel_execution_workflow(self, temp_dir, cli_runner):
        """Test executing parallel tasks."""
        os.chdir(temp_dir)

        config = temp_dir / "pyproject.toml"
        config.write_text(
            """
[tool.taskx.tasks]
lint = "echo 'Linting...'"
typecheck = "echo 'Type checking...'"
test = "echo 'Testing...'"
check = { parallel = ["lint", "typecheck", "test"], description = "Run all checks" }
"""
        )

        result = cli_runner.invoke(cli, ["run", "check"])

        assert result.exit_code == 0
        assert "Linting" in result.output
        assert "Type checking" in result.output
        assert "Testing" in result.output


# ============================================================================
# Test Development Workflows
# ============================================================================


@pytest.mark.integration
@pytest.mark.e2e
class TestDevelopmentWorkflows:
    """Test typical development workflows."""

    def test_dev_workflow_with_aliases(self, temp_dir, cli_runner):
        """Test development workflow using aliases."""
        os.chdir(temp_dir)

        config = temp_dir / "pyproject.toml"
        config.write_text(
            """
[tool.taskx.aliases]
t = "test"
f = "format"
l = "lint"

[tool.taskx.tasks]
test = "echo 'Running tests...'"
format = "echo 'Formatting code...'"
lint = "echo 'Linting code...'"
"""
        )

        # Use aliases
        result = cli_runner.invoke(cli, ["run", "t"])
        assert result.exit_code == 0
        assert "Running tests" in result.output

        result = cli_runner.invoke(cli, ["run", "f"])
        assert result.exit_code == 0
        assert "Formatting code" in result.output

        result = cli_runner.invoke(cli, ["run", "l"])
        assert result.exit_code == 0
        assert "Linting code" in result.output

    def test_ci_workflow(self, temp_dir, cli_runner):
        """Test CI/CD-like workflow."""
        os.chdir(temp_dir)

        config = temp_dir / "pyproject.toml"
        config.write_text(
            """
[tool.taskx.tasks]
install = "echo 'Installing dependencies...'"
lint = { depends = ["install"], cmd = "echo 'Linting...'" }
typecheck = { depends = ["install"], cmd = "echo 'Type checking...'" }
test = { depends = ["install"], cmd = "echo 'Testing...'" }
build = { depends = ["lint", "typecheck", "test"], cmd = "echo 'Building...'" }
ci = { depends = ["build"], cmd = "echo 'CI complete'" }
"""
        )

        result = cli_runner.invoke(cli, ["run", "ci"])

        assert result.exit_code == 0
        assert "Installing dependencies" in result.output
        assert "Linting" in result.output
        assert "Type checking" in result.output
        assert "Testing" in result.output
        assert "Building" in result.output
        assert "CI complete" in result.output


# ============================================================================
# Test Deployment Workflows
# ============================================================================


@pytest.mark.integration
@pytest.mark.e2e
class TestDeploymentWorkflows:
    """Test deployment workflows."""

    def test_deploy_with_confirmation(self, temp_dir, cli_runner):
        """Test deployment workflow with confirmation."""
        os.chdir(temp_dir)

        config = temp_dir / "pyproject.toml"
        config.write_text(
            """
[tool.taskx.tasks]
test = "echo 'Testing...'"
build = { depends = ["test"], cmd = "echo 'Building...'" }
deploy = { depends = ["build"], cmd = "echo 'Deploying...'", confirm = "Deploy to production?" }
"""
        )

        # Test with force flag (bypass confirmation)
        result = cli_runner.invoke(cli, ["run", "deploy", "--force"])

        assert result.exit_code == 0
        assert "Testing" in result.output
        assert "Building" in result.output
        assert "Deploying" in result.output

    def test_staged_deployment(self, temp_dir, cli_runner):
        """Test staged deployment workflow."""
        os.chdir(temp_dir)

        config = temp_dir / "pyproject.toml"
        config.write_text(
            """
[tool.taskx.env]
ENVIRONMENT = "production"

[tool.taskx.tasks]
test = "echo 'Testing...'"
build = { depends = ["test"], cmd = "echo 'Building...'" }
deploy-staging = { depends = ["build"], cmd = "echo 'Deploying to staging...'" }
deploy-prod = { depends = ["deploy-staging"], cmd = "echo 'Deploying to ${ENVIRONMENT}...'" }
"""
        )

        result = cli_runner.invoke(cli, ["run", "deploy-prod"])

        assert result.exit_code == 0
        assert "Testing" in result.output
        assert "Building" in result.output
        assert "Deploying to staging" in result.output
        assert "Deploying to production" in result.output


# ============================================================================
# Test Interactive Workflows
# ============================================================================


@pytest.mark.integration
@pytest.mark.e2e
class TestInteractiveWorkflows:
    """Test workflows with interactive prompts."""

    def test_interactive_build_with_version(self, temp_dir, cli_runner):
        """Test interactive build with version prompt."""
        os.chdir(temp_dir)

        config = temp_dir / "pyproject.toml"
        config.write_text(
            """
[tool.taskx.tasks.build]
cmd = "echo 'Building version ${VERSION}...'"

[tool.taskx.tasks.build.prompt]
VERSION = { type = "text", message = "Version number:", default = "1.0.0" }
"""
        )

        # Provide version via env override (simulates non-interactive)
        result = cli_runner.invoke(cli, ["run", "build", "--env", "VERSION=2.0.0"])

        assert result.exit_code == 0
        assert "Building version 2.0.0" in result.output

    def test_multi_prompt_workflow(self, temp_dir, cli_runner):
        """Test workflow with multiple prompts."""
        os.chdir(temp_dir)

        config = temp_dir / "pyproject.toml"
        config.write_text(
            """
[tool.taskx.tasks.deploy]
cmd = "echo 'Deploying ${APP} version ${VERSION} to ${ENV}'"

[tool.taskx.tasks.deploy.prompt]
APP = { type = "text", message = "App name:", default = "myapp" }
VERSION = { type = "text", message = "Version:", default = "1.0.0" }
ENV = { type = "select", message = "Environment:", choices = ["dev", "staging", "prod"], default = "dev" }
"""
        )

        result = cli_runner.invoke(
            cli,
            ["run", "deploy", "--env", "APP=webapp", "--env", "VERSION=3.0.0", "--env", "ENV=prod"],
        )

        assert result.exit_code == 0
        assert "Deploying webapp version 3.0.0 to prod" in result.output


# ============================================================================
# Test Documentation Workflows
# ============================================================================


@pytest.mark.integration
@pytest.mark.e2e
class TestDocumentationWorkflows:
    """Test documentation and help workflows."""

    def test_list_tasks_workflow(self, temp_dir, cli_runner):
        """Test listing tasks workflow."""
        os.chdir(temp_dir)

        config = temp_dir / "pyproject.toml"
        config.write_text(
            """
[tool.taskx.aliases]
t = "test"

[tool.taskx.tasks]
test = { cmd = "echo test", description = "Run all tests" }
build = { cmd = "echo build", description = "Build the project" }
"""
        )

        result = cli_runner.invoke(cli, ["list"])

        assert result.exit_code == 0
        assert "test" in result.output
        assert "build" in result.output
        assert "Run all tests" in result.output
        assert "Build the project" in result.output

    def test_completion_generation_workflow(self, temp_dir, cli_runner):
        """Test generating completion scripts."""
        os.chdir(temp_dir)

        config = temp_dir / "pyproject.toml"
        config.write_text(
            """
[tool.taskx.tasks]
test = "echo test"
"""
        )

        # Generate bash completion
        result = cli_runner.invoke(cli, ["completion", "bash"])
        assert result.exit_code == 0
        assert len(result.output) > 100

        # Generate zsh completion
        result = cli_runner.invoke(cli, ["completion", "zsh"])
        assert result.exit_code == 0
        assert len(result.output) > 100


# ============================================================================
# Test Error Handling Workflows
# ============================================================================


@pytest.mark.integration
@pytest.mark.e2e
class TestErrorHandlingWorkflows:
    """Test workflows with error conditions."""

    def test_missing_config_workflow(self, temp_dir, cli_runner):
        """Test workflow when config file is missing."""
        os.chdir(temp_dir)

        result = cli_runner.invoke(cli, ["list"])

        assert result.exit_code != 0
        assert "not found" in result.output.lower() or "does not exist" in result.output.lower()

    def test_invalid_task_workflow(self, temp_dir, cli_runner):
        """Test workflow with non-existent task."""
        os.chdir(temp_dir)

        config = temp_dir / "pyproject.toml"
        config.write_text(
            """
[tool.taskx.tasks]
test = "echo test"
"""
        )

        result = cli_runner.invoke(cli, ["run", "nonexistent"])

        assert result.exit_code != 0
        assert "not found" in result.output.lower() or "unknown" in result.output.lower()

    def test_task_failure_workflow(self, temp_dir, cli_runner):
        """Test workflow when task fails."""
        os.chdir(temp_dir)

        config = temp_dir / "pyproject.toml"
        config.write_text(
            """
[tool.taskx.tasks]
fail = "exit 1"
"""
        )

        result = cli_runner.invoke(cli, ["run", "fail"])

        assert result.exit_code != 0


# ============================================================================
# Test Complex Real-World Workflows
# ============================================================================


@pytest.mark.integration
@pytest.mark.e2e
class TestRealWorldWorkflows:
    """Test complex real-world scenarios."""

    def test_python_package_release_workflow(self, temp_dir, cli_runner):
        """Test complete Python package release workflow."""
        os.chdir(temp_dir)

        config = temp_dir / "pyproject.toml"
        config.write_text(
            """
[tool.taskx.env]
VERSION = "1.0.0"

[tool.taskx.aliases]
rel = "release"

[tool.taskx.tasks]
clean = "echo 'Cleaning build artifacts...'"
format = "echo 'Formatting code...'"
lint = "echo 'Linting...'"
typecheck = "echo 'Type checking...'"
test = "echo 'Running tests...'"
check = { parallel = ["format", "lint", "typecheck", "test"], description = "Run all checks" }
build = { depends = ["check", "clean"], cmd = "echo 'Building version ${VERSION}...'" }
publish-test = { depends = ["build"], cmd = "echo 'Publishing to TestPyPI...'" }
release = { depends = ["publish-test"], cmd = "echo 'Released ${VERSION}'", confirm = "Release version ${VERSION}?" }
"""
        )

        result = cli_runner.invoke(cli, ["run", "rel", "--force"])

        assert result.exit_code == 0
        assert "Cleaning" in result.output
        assert "Formatting" in result.output
        assert "Linting" in result.output
        assert "Type checking" in result.output
        assert "Running tests" in result.output
        assert "Building version 1.0.0" in result.output
        assert "Publishing to TestPyPI" in result.output
        assert "Released 1.0.0" in result.output

    def test_web_app_development_workflow(self, temp_dir, cli_runner):
        """Test web application development workflow."""
        os.chdir(temp_dir)

        config = temp_dir / "pyproject.toml"
        config.write_text(
            """
[tool.taskx.tasks]
install = "echo 'Installing dependencies...'"
db-setup = "echo 'Setting up database...'"
db-migrate = "echo 'Running migrations...'"
dev = { depends = ["install", "db-setup", "db-migrate"], cmd = "echo 'Starting dev server...'" }
test = "echo 'Running tests...'"
"""
        )

        # Setup and start dev server
        result = cli_runner.invoke(cli, ["run", "dev"])

        assert result.exit_code == 0
        assert "Installing dependencies" in result.output
        assert "Setting up database" in result.output
        assert "Running migrations" in result.output
        assert "Starting dev server" in result.output

        # Run tests
        result = cli_runner.invoke(cli, ["run", "test"])
        assert result.exit_code == 0
        assert "Running tests" in result.output
