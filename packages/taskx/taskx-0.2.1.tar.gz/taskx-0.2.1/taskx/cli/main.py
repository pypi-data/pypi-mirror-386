"""
Main CLI entry point for taskx.

Copyright (c) 2025 taskx Project
Licensed under Proprietary License - See LICENSE file

This software is free to use but cannot be modified, copied, or redistributed.
License notices must be preserved in all uses. See LICENSE file for full terms.
"""

import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console

from taskx import __version__
from taskx.cli.commands.completion import completion
from taskx.cli.commands.graph import graph
from taskx.cli.commands.watch import watch
from taskx.core.config import Config, ConfigError
from taskx.core.prompts import PromptConfig, PromptManager
from taskx.core.runner import TaskRunner
from taskx.formatters.console import ConsoleFormatter
from taskx.templates import get_template
from taskx.templates import list_templates as get_template_list


@click.group(invoke_without_command=True)
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=False),
    default="pyproject.toml",
    help="Path to configuration file",
)
@click.option("--version", "-v", is_flag=True, help="Show version and exit")
@click.pass_context
def cli(ctx: click.Context, config: str, version: bool) -> None:
    """
    taskx - Modern Python Task Runner

    npm scripts for Python. Simple task automation that just works.
    """
    # Store config path in context
    ctx.ensure_object(dict)
    ctx.obj["config_path"] = Path(config)
    ctx.obj["console"] = Console()
    ctx.obj["formatter"] = ConsoleFormatter(ctx.obj["console"])

    # Show version if requested
    if version:
        click.echo(f"taskx version {__version__}")
        ctx.exit(0)

    # If no subcommand, show available tasks
    if ctx.invoked_subcommand is None:
        try:
            cfg = Config(ctx.obj["config_path"])
            cfg.load()
            ctx.obj["formatter"].print_task_list(cfg.tasks, cfg.aliases)
        except (FileNotFoundError, ConfigError) as e:
            ctx.obj["formatter"].print_error(str(e))
            click.echo("\nHint: Run 'taskx init' to create a configuration file")
            ctx.exit(1)


@cli.command()
@click.option("--names-only", is_flag=True, help="Output only task names (one per line)")
@click.option("--include-aliases", is_flag=True, help="Include aliases in output")
@click.pass_context
def list(ctx: click.Context, names_only: bool, include_aliases: bool) -> None:
    """List all available tasks."""
    try:
        cfg = Config(ctx.obj["config_path"])
        cfg.load()

        if names_only:
            # Output only task names (for shell completion)
            task_names = sorted(cfg.tasks.keys())
            for name in task_names:
                click.echo(name)

            # Optionally include aliases
            if include_aliases and cfg.aliases:
                for alias in sorted(cfg.aliases.keys()):
                    click.echo(alias)
        else:
            # Show task list with aliases
            ctx.obj["formatter"].print_task_list(cfg.tasks, cfg.aliases)
    except (FileNotFoundError, ConfigError) as e:
        ctx.obj["formatter"].print_error(str(e))
        ctx.exit(1)


@cli.command(context_settings=dict(ignore_unknown_options=True, allow_extra_args=True))
@click.argument("task_name")
@click.option("--env", "-e", multiple=True, help="Set environment variable (KEY=VALUE)")
@click.pass_context
def run(ctx: click.Context, task_name: str, env: tuple) -> None:
    """Run a specific task."""
    try:
        # Load configuration
        cfg = Config(ctx.obj["config_path"])
        cfg.load()

        # Resolve alias to actual task name
        original_name = task_name
        actual_task_name = cfg.resolve_alias(task_name)

        # Check if task exists
        if actual_task_name not in cfg.tasks:
            ctx.obj["formatter"].print_error(f"Task '{task_name}' not found")
            click.echo(f"\nAvailable tasks: {', '.join(sorted(cfg.tasks.keys()))}")
            if cfg.aliases:
                click.echo(f"Available aliases: {', '.join(sorted(cfg.aliases.keys()))}")
            ctx.exit(1)

        # Show alias resolution if used
        if actual_task_name != original_name:
            click.echo(f"→ Alias '{original_name}' resolves to task '{actual_task_name}'")

        # Parse environment overrides
        env_overrides = {}
        for e in env:
            if "=" in e:
                key, value = e.split("=", 1)
                env_overrides[key] = value

        # Run task
        runner = TaskRunner(cfg, ctx.obj["console"])
        success = runner.run(actual_task_name, env_overrides)

        if not success:
            ctx.exit(1)

    except (FileNotFoundError, ConfigError) as e:
        ctx.obj["formatter"].print_error(str(e))
        ctx.exit(1)
    except KeyboardInterrupt:
        ctx.obj["formatter"].print_warning("\nTask interrupted by user")
        ctx.exit(130)  # Standard exit code for SIGINT
    except Exception as e:
        ctx.obj["formatter"].print_error(f"Unexpected error: {e}")
        ctx.exit(1)


@cli.command()
@click.option("--name", "-n", help="Project name")
@click.option(
    "--examples/--no-examples",
    default=True,
    help="Add example tasks (when not using template)",
)
@click.option(
    "--template", "-t", help="Use project template (django, fastapi, data-science, python-library)"
)
@click.option("--list-templates", is_flag=True, help="List available templates and exit")
@click.pass_context
def init(
    ctx: click.Context,
    name: Optional[str],
    examples: bool,
    template: Optional[str],
    list_templates: bool,
) -> None:
    """Initialize taskx configuration in current directory."""
    # Show available templates if requested
    if list_templates:
        templates = get_template_list()
        click.echo("Available templates:\n")

        # Group by category
        from collections import defaultdict

        by_category = defaultdict(list)
        for t in templates:
            by_category[t["category"]].append(t)

        for category in sorted(by_category.keys()):
            click.echo(f"  {category.upper()}:")
            for t in by_category[category]:
                click.echo(f"    {t['name']:<20} {t['description']}")
            click.echo()

        click.echo("Usage: taskx init --template <name>")
        ctx.exit(0)

    config_path = Path("pyproject.toml")

    if config_path.exists():
        if not click.confirm(f"{config_path} already exists. Overwrite?"):
            ctx.obj["formatter"].print_warning("Initialization cancelled")
            ctx.exit(0)

    # Use template if provided
    if template:
        template_obj = get_template(template)
        if not template_obj:
            ctx.obj["formatter"].print_error(f"Template '{template}' not found")
            click.echo("\nRun 'taskx init --list-templates' to see available templates")
            ctx.exit(1)

        # Get prompts from template
        prompt_configs = {}
        for var_name, prompt_def in template_obj.get_prompts().items():
            prompt_configs[var_name] = PromptConfig(
                type=prompt_def["type"],
                message=prompt_def["message"],
                choices=prompt_def.get("choices"),
                default=prompt_def.get("default"),
            )

        # Prompt user for template variables
        try:
            prompt_manager = PromptManager()
            variables = prompt_manager.prompt_for_variables(prompt_configs)
        except KeyboardInterrupt:
            ctx.obj["formatter"].print_warning("\nInitialization cancelled by user")
            ctx.exit(130)

        # Generate pyproject.toml from template
        content = template_obj.generate(variables)
        config_path.write_text(content)

        # Create additional files (README, .gitignore, etc.)
        additional_files = template_obj.get_additional_files(variables)
        for file_path_str, file_content in additional_files.items():
            file_path = Path(file_path_str)

            # Create parent directories if needed
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # Write file
            file_path.write_text(file_content)
            click.echo(f"  Created: {file_path}")

        ctx.obj["formatter"].print_success(f"Created {template} project with taskx configuration")
        click.echo("\nNext steps:")
        click.echo("  1. Review pyproject.toml and adjust as needed")
        click.echo("  2. Run 'taskx list' to see available tasks")
        click.echo("  3. Run 'taskx <task-name>' to execute a task")

    else:
        # Original behavior: create basic config
        project_name = name
        if not project_name:
            project_name = click.prompt("Project name", default="myproject")

        # Create basic pyproject.toml with taskx section
        content = f"""[project]
name = "{project_name}"
version = "0.1.0"

[tool.taskx.env]
PROJECT_NAME = "{project_name}"

[tool.taskx.tasks]
"""

        if examples:
            content += """# Development tasks
dev = { cmd = "echo 'Development server would start here'", description = "Start development server" }
test = { cmd = "pytest tests/", description = "Run test suite" }
lint = { cmd = "ruff check .", description = "Run linting" }
format = { cmd = "black . && isort .", description = "Format code" }

# Build tasks
build = { cmd = "python -m build", description = "Build distribution packages" }
clean = { cmd = "rm -rf dist build *.egg-info", description = "Clean build artifacts" }

# Composite task with dependencies
check = { depends = ["lint", "test"], cmd = "echo 'All checks passed!'", description = "Run all checks" }
"""
        else:
            content += """hello = "echo 'Hello from taskx!'"
"""

        config_path.write_text(content)
        ctx.obj["formatter"].print_success(f"Created {config_path} with taskx configuration")
        click.echo("\nNext steps:")
        click.echo("  1. Edit pyproject.toml to add your tasks")
        click.echo("  2. Run 'taskx list' to see available tasks")
        click.echo("  3. Run 'taskx <task-name>' to execute a task")


# Register additional commands
cli.add_command(watch)
cli.add_command(graph)
cli.add_command(completion)


# Register task names as dynamic commands
@cli.command(name="__dynamic__", hidden=True, add_help_option=False)
@click.argument("task_name", required=False)
@click.pass_context
def dynamic_task(ctx: click.Context, task_name: Optional[str]) -> None:
    """Handle dynamic task execution."""
    if task_name:
        ctx.invoke(run, task_name=task_name)


def main() -> int:
    """Main entry point."""
    try:
        cli(obj={})
        return 0
    except SystemExit as e:
        return e.code if isinstance(e.code, int) else 1
    except Exception as e:
        console = Console()
        console.print(f"[red]Fatal error: {e}[/red]")
        return 1


if __name__ == "__main__":
    sys.exit(main())
