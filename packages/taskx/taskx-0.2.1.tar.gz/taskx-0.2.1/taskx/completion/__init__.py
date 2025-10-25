"""
Shell completion module for taskx.

Provides tab-completion support for:
- Bash
- Zsh
- Fish
- PowerShell

Copyright (c) 2025 taskx Project
Licensed under Proprietary License - See LICENSE file
"""

from taskx.completion.base import CompletionGenerator
from taskx.completion.bash import BashCompletion
from taskx.completion.fish import FishCompletion
from taskx.completion.powershell import PowerShellCompletion
from taskx.completion.zsh import ZshCompletion

__all__ = [
    "CompletionGenerator",
    "BashCompletion",
    "ZshCompletion",
    "FishCompletion",
    "PowerShellCompletion",
]
