"""
Base completion generator for shell completion scripts.

Copyright (c) 2025 taskx Project
Licensed under Proprietary License - See LICENSE file
"""

from abc import ABC, abstractmethod
from typing import Dict, List

from taskx.core.config import Config


class CompletionGenerator(ABC):
    """Base class for shell completion generators."""

    def __init__(self, config: Config):
        """
        Initialize completion generator.

        Args:
            config: Loaded taskx configuration
        """
        self.config = config

    @abstractmethod
    def generate(self) -> str:
        """
        Generate completion script for shell.

        Returns:
            Completion script as string
        """
        pass

    def get_tasks(self) -> List[str]:
        """
        Get list of task names from configuration.

        Returns:
            Sorted list of task names
        """
        return sorted(self.config.tasks.keys())

    def get_commands(self) -> List[str]:
        """
        Get list of taskx commands.

        Returns:
            List of command names
        """
        return ["list", "run", "watch", "graph", "init", "completion"]

    def get_graph_formats(self) -> List[str]:
        """
        Get available graph output formats.

        Returns:
            List of format names
        """
        return ["tree", "mermaid", "dot"]

    def get_aliases(self) -> Dict[str, str]:
        """
        Get alias mappings if available.

        Returns:
            Dict mapping alias to task name
        """
        if hasattr(self.config, "aliases") and self.config.aliases:
            return self.config.aliases
        return {}
