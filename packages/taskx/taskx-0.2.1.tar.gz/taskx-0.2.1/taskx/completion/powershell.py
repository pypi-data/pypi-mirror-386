"""
PowerShell completion generator for taskx.

Copyright (c) 2025 taskx Project
Licensed under Proprietary License - See LICENSE file
"""

from taskx.completion.base import CompletionGenerator


class PowerShellCompletion(CompletionGenerator):
    """PowerShell completion script generator."""

    def generate(self) -> str:
        """
        Generate PowerShell completion script.

        Supports:
        - Command completion
        - Task name completion
        - Parameter completion
        - Windows-specific features

        Returns:
            PowerShell completion script
        """
        script = """# taskx PowerShell completion script
# Add to your PowerShell profile: $PROFILE

# Register argument completer for taskx
Register-ArgumentCompleter -Native -CommandName taskx -ScriptBlock {
    param($wordToComplete, $commandAst, $cursorPosition)

    $commands = @('list', 'run', 'watch', 'graph', 'init', 'completion', '--version', '--help')
    $graphFormats = @('tree', 'mermaid', 'dot')
    $shells = @('bash', 'zsh', 'fish', 'powershell')

    # Get the command elements
    $elements = $commandAst.CommandElements
    $commandCount = $elements.Count

    # If only 'taskx' has been typed, suggest main commands
    if ($commandCount -eq 1) {
        $commands | Where-Object { $_ -like "$wordToComplete*" } | ForEach-Object {
            [System.Management.Automation.CompletionResult]::new($_, $_, 'ParameterValue', $_)
        }
        return
    }

    # Get the subcommand (second element)
    $subcommand = $elements[1].ToString()

    switch ($subcommand) {
        'run' {
            # Complete with task names
            if ($commandCount -eq 2) {
                try {
                    $tasks = & taskx list --names-only 2>$null
                    $tasks | Where-Object { $_ -like "$wordToComplete*" } | ForEach-Object {
                        [System.Management.Automation.CompletionResult]::new($_, $_, 'ParameterValue', $_)
                    }
                } catch {
                    # Ignore errors
                }
            }
        }
        'watch' {
            # Complete with task names
            if ($commandCount -eq 2) {
                try {
                    $tasks = & taskx list --names-only 2>$null
                    $tasks | Where-Object { $_ -like "$wordToComplete*" } | ForEach-Object {
                        [System.Management.Automation.CompletionResult]::new($_, $_, 'ParameterValue', $_)
                    }
                } catch {
                    # Ignore errors
                }
            }
        }
        'graph' {
            # Handle graph options
            if ($wordToComplete -match '^--') {
                @('--format', '--task', '--help') | Where-Object { $_ -like "$wordToComplete*" } | ForEach-Object {
                    [System.Management.Automation.CompletionResult]::new($_, $_, 'ParameterValue', $_)
                }
            } elseif ($elements[-2].ToString() -eq '--format') {
                # Complete with format names
                $graphFormats | Where-Object { $_ -like "$wordToComplete*" } | ForEach-Object {
                    [System.Management.Automation.CompletionResult]::new($_, $_, 'ParameterValue', $_)
                }
            } elseif ($elements[-2].ToString() -eq '--task') {
                # Complete with task names
                try {
                    $tasks = & taskx list --names-only 2>$null
                    $tasks | Where-Object { $_ -like "$wordToComplete*" } | ForEach-Object {
                        [System.Management.Automation.CompletionResult]::new($_, $_, 'ParameterValue', $_)
                    }
                } catch {
                    # Ignore errors
                }
            }
        }
        'list' {
            # Complete with list options
            if ($wordToComplete -match '^--') {
                @('--names-only', '--include-aliases', '--help') | Where-Object { $_ -like "$wordToComplete*" } | ForEach-Object {
                    [System.Management.Automation.CompletionResult]::new($_, $_, 'ParameterValue', $_)
                }
            }
        }
        'init' {
            # Complete with init options
            if ($wordToComplete -match '^--') {
                @('--name', '--examples', '--no-examples', '--help') | Where-Object { $_ -like "$wordToComplete*" } | ForEach-Object {
                    [System.Management.Automation.CompletionResult]::new($_, $_, 'ParameterValue', $_)
                }
            }
        }
        'completion' {
            # Complete with shell names
            if ($commandCount -eq 2) {
                $shells | Where-Object { $_ -like "$wordToComplete*" } | ForEach-Object {
                    [System.Management.Automation.CompletionResult]::new($_, $_, 'ParameterValue', $_)
                }
            } elseif ($wordToComplete -match '^--') {
                @('--install', '--help') | Where-Object { $_ -like "$wordToComplete*" } | ForEach-Object {
                    [System.Management.Automation.CompletionResult]::new($_, $_, 'ParameterValue', $_)
                }
            }
        }
    }
}

Write-Host "taskx completion loaded for PowerShell" -ForegroundColor Green
"""
        return script
