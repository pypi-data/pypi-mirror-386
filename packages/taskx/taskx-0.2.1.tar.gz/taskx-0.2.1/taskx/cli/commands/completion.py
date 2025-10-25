"""
Shell completion command for taskx.

Copyright (c) 2025 taskx Project
Licensed under Proprietary License - See LICENSE file
"""

import sys
from pathlib import Path

import click

from taskx.completion import (
    BashCompletion,
    FishCompletion,
    PowerShellCompletion,
    ZshCompletion,
)
from taskx.core.config import Config


@click.command()
@click.argument("shell", type=click.Choice(["bash", "zsh", "fish", "powershell"]))
@click.option("--install", is_flag=True, help="Install completion script to system")
@click.pass_context
def completion(ctx: click.Context, shell: str, install: bool) -> None:
    """
    Generate shell completion script.

    Supports bash, zsh, fish, and powershell.

    Examples:
        taskx completion bash                # Print bash completion script
        taskx completion bash --install      # Install bash completion
        taskx completion zsh > _taskx        # Save zsh completion to file
    """
    try:
        # Load config (may not exist, but that's OK for completion)
        config_path = ctx.obj.get("config_path", Path("pyproject.toml"))
        try:
            config = Config(config_path)
            config.load()
        except (FileNotFoundError, Exception):
            # Create empty config for completion generation
            config = Config(config_path)
            config.tasks = {}

        # Generate completion script
        if shell == "bash":
            generator = BashCompletion(config)
        elif shell == "zsh":
            generator = ZshCompletion(config)
        elif shell == "fish":
            generator = FishCompletion(config)
        elif shell == "powershell":
            generator = PowerShellCompletion(config)
        else:
            click.echo(f"Shell '{shell}' not supported", err=True)
            ctx.exit(1)

        script = generator.generate()

        if install:
            # Install completion script
            try:
                install_path = install_completion(shell, script)
                click.echo(f"✓ Completion installed: {install_path}")
                click.echo()
                click.echo("To activate completion, restart your shell or run:")
                if shell == "bash":
                    click.echo(f"  source {install_path}")
                elif shell == "zsh":
                    click.echo("  Restart your shell or run: exec zsh")
                elif shell == "fish":
                    click.echo("  Completion will be available immediately")
                elif shell == "powershell":
                    click.echo("  Restart PowerShell or run: . $PROFILE")
            except PermissionError as e:
                click.echo(f"✗ Permission denied: {e}", err=True)
                click.echo()
                click.echo("Try one of these alternatives:")
                click.echo(f"  1. Print to file: taskx completion {shell} > completion.{shell}")
                click.echo("  2. Install manually with sudo")
                ctx.exit(1)
            except Exception as e:
                click.echo(f"✗ Installation failed: {e}", err=True)
                ctx.exit(1)
        else:
            # Print to stdout
            click.echo(script)

    except Exception as e:
        formatter = ctx.obj.get("formatter")
        if formatter:
            formatter.print_error(f"Completion generation failed: {e}")
        else:
            click.echo(f"Error: {e}", err=True)
        ctx.exit(1)


def install_completion(shell: str, script: str) -> Path:
    """
    Install completion script to appropriate system location.

    Args:
        shell: Shell type (bash, zsh, fish, powershell)
        script: Completion script content

    Returns:
        Path where script was installed

    Raises:
        PermissionError: If cannot write to install location
        FileNotFoundError: If no suitable install location found
    """
    home = Path.home()

    # Define installation paths (try in order)
    paths = {
        "bash": [
            home / ".local/share/bash-completion/completions/taskx",
            home / ".bash_completion.d/taskx",
        ],
        "zsh": [
            home / ".zsh/completion/_taskx",
            home / ".oh-my-zsh/completions/_taskx",
        ],
        "fish": [
            home / ".config/fish/completions/taskx.fish",
        ],
        "powershell": [
            home / "Documents/PowerShell/Completions/taskx_completion.ps1",
            home / "Documents/WindowsPowerShell/Completions/taskx_completion.ps1",
        ],
    }

    if shell not in paths:
        raise ValueError(f"Unsupported shell: {shell}")

    # Try each path in order
    last_error = None
    for install_path in paths[shell]:
        try:
            # Create parent directory if needed
            install_path.parent.mkdir(parents=True, exist_ok=True)

            # Write script
            install_path.write_text(script, encoding="utf-8")

            # Make executable (Unix only)
            if sys.platform != "win32":
                install_path.chmod(0o644)

            return install_path

        except PermissionError as e:
            last_error = e
            continue
        except Exception as e:
            last_error = e
            continue

    # If we get here, all paths failed
    if last_error:
        raise last_error
    raise FileNotFoundError(f"No suitable install location found for {shell}")
