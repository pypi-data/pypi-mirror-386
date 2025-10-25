"""
Fish completion generator for taskx.

Copyright (c) 2025 taskx Project
Licensed under Proprietary License - See LICENSE file
"""

from taskx.completion.base import CompletionGenerator


class FishCompletion(CompletionGenerator):
    """Fish shell completion script generator."""

    def generate(self) -> str:
        """
        Generate fish completion script.

        Supports:
        - Command completion with descriptions
        - Dynamic task name completion
        - Condition-based completion
        - Modern fish shell features

        Returns:
            Fish completion script
        """
        script = """# taskx fish completion script
# Install to ~/.config/fish/completions/taskx.fish

# Disable file completion by default
complete -c taskx -f

# Main commands
complete -c taskx -n "__fish_use_subcommand" -a "list" -d "List all available tasks"
complete -c taskx -n "__fish_use_subcommand" -a "run" -d "Run a specific task"
complete -c taskx -n "__fish_use_subcommand" -a "watch" -d "Watch files and auto-restart task"
complete -c taskx -n "__fish_use_subcommand" -a "graph" -d "Visualize task dependencies"
complete -c taskx -n "__fish_use_subcommand" -a "init" -d "Initialize taskx configuration"
complete -c taskx -n "__fish_use_subcommand" -a "completion" -d "Generate shell completion script"

# Global options
complete -c taskx -s v -l version -d "Show version and exit"
complete -c taskx -s h -l help -d "Show help message"
complete -c taskx -s c -l config -d "Path to configuration file" -r -F

# 'list' command options
complete -c taskx -n "__fish_seen_subcommand_from list" -l names-only -d "Output only task names"
complete -c taskx -n "__fish_seen_subcommand_from list" -l include-aliases -d "Include aliases in output"

# 'run' command - complete with task names
complete -c taskx -n "__fish_seen_subcommand_from run" -a "(taskx list --names-only 2>/dev/null)"
complete -c taskx -n "__fish_seen_subcommand_from run" -s e -l env -d "Set environment variable"

# 'watch' command - complete with task names
complete -c taskx -n "__fish_seen_subcommand_from watch" -a "(taskx list --names-only 2>/dev/null)"

# 'graph' command options
complete -c taskx -n "__fish_seen_subcommand_from graph" -l format -d "Output format" -a "tree mermaid dot"
complete -c taskx -n "__fish_seen_subcommand_from graph" -l task -d "Show dependencies for specific task" -a "(taskx list --names-only 2>/dev/null)"

# 'init' command options
complete -c taskx -n "__fish_seen_subcommand_from init" -s n -l name -d "Project name"
complete -c taskx -n "__fish_seen_subcommand_from init" -l examples -d "Add example tasks"
complete -c taskx -n "__fish_seen_subcommand_from init" -l no-examples -d "Do not add example tasks"

# 'completion' command - complete with shell names
complete -c taskx -n "__fish_seen_subcommand_from completion" -a "bash zsh fish powershell" -d "Shell type"
complete -c taskx -n "__fish_seen_subcommand_from completion" -l install -d "Install completion script"
"""
        return script
