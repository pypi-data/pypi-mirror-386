"""
Bash completion generator for taskx.

Copyright (c) 2025 taskx Project
Licensed under Proprietary License - See LICENSE file
"""

from taskx.completion.base import CompletionGenerator


class BashCompletion(CompletionGenerator):
    """Bash completion script generator."""

    def generate(self) -> str:
        """
        Generate bash completion script.

        Supports:
        - Command completion (list, run, watch, etc.)
        - Task name completion after 'run' and 'watch'
        - Option completion for various commands
        - Graph format completion

        Returns:
            Bash completion script
        """
        commands = " ".join(self.get_commands())
        graph_formats = " ".join(self.get_graph_formats())

        script = f"""# taskx bash completion script
# Source this file or install to ~/.local/share/bash-completion/completions/taskx

_taskx_completion() {{
    local cur prev words cword
    _init_completion || return

    # Main commands and options
    local commands="{commands} --version --help"

    # If we're completing the first argument
    if [ $cword -eq 1 ]; then
        COMPREPLY=( $(compgen -W "$commands" -- "$cur") )
        return
    fi

    # Handle completion based on previous word
    case "$prev" in
        run|watch)
            # Complete with task names
            local tasks="$(taskx list --names-only 2>/dev/null || echo "")"
            COMPREPLY=( $(compgen -W "$tasks" -- "$cur") )
            return
            ;;
        graph)
            # Complete with graph options
            local options="--format --task --help"
            COMPREPLY=( $(compgen -W "$options" -- "$cur") )
            return
            ;;
        --format)
            # Complete with graph formats
            local formats="{graph_formats}"
            COMPREPLY=( $(compgen -W "$formats" -- "$cur") )
            return
            ;;
        --task)
            # Complete with task names for graph
            local tasks="$(taskx list --names-only 2>/dev/null || echo "")"
            COMPREPLY=( $(compgen -W "$tasks" -- "$cur") )
            return
            ;;
        completion)
            # Complete with shell names
            local shells="bash zsh fish powershell --install --help"
            COMPREPLY=( $(compgen -W "$shells" -- "$cur") )
            return
            ;;
        --config|-c)
            # Complete with .toml files
            COMPREPLY=( $(compgen -f -X '!*.toml' -- "$cur") )
            return
            ;;
    esac

    # Default: complete with commands if nothing else matches
    COMPREPLY=( $(compgen -W "$commands" -- "$cur") )
}}

# Register the completion function
complete -F _taskx_completion taskx

# Also handle 'python -m taskx' invocation
complete -F _taskx_completion -o default python -m taskx
"""
        return script
