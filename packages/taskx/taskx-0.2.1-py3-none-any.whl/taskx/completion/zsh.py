"""
Zsh completion generator for taskx.

Copyright (c) 2025 taskx Project
Licensed under Proprietary License - See LICENSE file
"""

from taskx.completion.base import CompletionGenerator


class ZshCompletion(CompletionGenerator):
    """Zsh completion script generator."""

    def generate(self) -> str:
        """
        Generate zsh completion script.

        Supports:
        - Command completion with descriptions
        - Task name completion
        - Option completion with help text
        - Smart context-aware completion

        Returns:
            Zsh completion script
        """
        script = """#compdef taskx

# taskx zsh completion script
# Install to ~/.zsh/completion/_taskx or ~/.oh-my-zsh/completions/_taskx

_taskx() {
    local context state line
    typeset -A opt_args

    _arguments -C \\
        '1: :->command' \\
        '*:: :->args'

    case $state in
        command)
            local -a commands
            commands=(
                'list:List all available tasks'
                'run:Run a specific task'
                'watch:Watch files and auto-restart task on changes'
                'graph:Visualize task dependencies'
                'init:Initialize taskx configuration'
                'completion:Generate shell completion script'
                '--version:Show version and exit'
                '--help:Show help message'
            )
            _describe 'command' commands
            ;;
        args)
            case $line[1] in
                list)
                    _arguments \\
                        '--names-only[Output only task names]' \\
                        '--include-aliases[Include aliases in output]' \\
                        '--help[Show help message]'
                    ;;
                run|watch)
                    # Complete with task names
                    local -a tasks
                    tasks=(${(f)"$(taskx list --names-only 2>/dev/null || echo "")"})
                    _describe 'task' tasks
                    _arguments \\
                        '--env[Set environment variable]:env:' \\
                        '--help[Show help message]'
                    ;;
                graph)
                    _arguments \\
                        '--format[Output format]:format:(tree mermaid dot)' \\
                        '--task[Show dependencies for specific task]:task:' \\
                        '--help[Show help message]'
                    ;;
                init)
                    _arguments \\
                        '--name[Project name]:name:' \\
                        '--examples[Add example tasks]' \\
                        '--no-examples[Do not add example tasks]' \\
                        '--help[Show help message]'
                    ;;
                completion)
                    _arguments \\
                        '1:shell:(bash zsh fish powershell)' \\
                        '--install[Install completion script]' \\
                        '--help[Show help message]'
                    ;;
            esac
            ;;
    esac
}

_taskx

# Handle both 'taskx' and 'python -m taskx' invocations
compdef _taskx taskx
compdef _taskx python -m taskx
"""
        return script
