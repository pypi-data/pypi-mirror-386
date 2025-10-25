"""
Base template class for project templates.

Copyright (c) 2025 taskx Project
Licensed under Proprietary License - See LICENSE file
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict

from jinja2.sandbox import SandboxedEnvironment


class Template(ABC):
    """Base class for project templates."""

    # Template metadata
    name: str = ""
    description: str = ""
    category: str = ""  # e.g., "web", "data", "library"

    def __init__(self) -> None:
        """Initialize template."""
        if not self.name:
            raise ValueError(f"{self.__class__.__name__} must define 'name' attribute")
        if not self.description:
            raise ValueError(f"{self.__class__.__name__} must define 'description' attribute")

    @abstractmethod
    def get_prompts(self) -> Dict[str, Any]:
        """
        Get prompts for template variables.

        Returns:
            Dictionary of variable names to prompt configurations
            Format: {
                "var_name": {
                    "type": "text" | "select" | "confirm",
                    "message": "Prompt message",
                    "default": "default value",
                    "choices": ["choice1", "choice2"]  # for select type
                }
            }
        """
        pass

    @abstractmethod
    def generate(self, variables: Dict[str, str]) -> str:
        """
        Generate pyproject.toml content from template.

        Args:
            variables: User-provided variable values

        Returns:
            Generated pyproject.toml content
        """
        pass

    def get_additional_files(self, variables: Dict[str, str]) -> Dict[str, str]:
        """
        Get additional files to create (optional).

        Args:
            variables: User-provided variable values

        Returns:
            Dictionary mapping file paths to file contents
        """
        return {}

    def validate_variables(self, variables: Dict[str, str]) -> None:
        """
        Validate template variables (optional override).

        Args:
            variables: User-provided variable values

        Raises:
            ValueError: If validation fails
        """
        pass

    def render_template(self, template_str: str, variables: Dict[str, str]) -> str:
        """
        Render a Jinja2 template string with variables.

        Args:
            template_str: Jinja2 template string
            variables: Variables to substitute

        Returns:
            Rendered template
        """
        # Use sandboxed environment for security
        env = SandboxedEnvironment()
        template = env.from_string(template_str)
        return template.render(**variables)

    def load_template_file(self, filename: str) -> str:
        """
        Load template file from template directory.

        Args:
            filename: Template filename (e.g., "pyproject.toml.j2")

        Returns:
            Template file contents
        """
        template_dir = Path(__file__).parent / self.name
        template_path = template_dir / filename

        if not template_path.exists():
            raise FileNotFoundError(f"Template file not found: {template_path}")

        return template_path.read_text(encoding="utf-8")


def get_template_dir() -> Path:
    """Get the templates directory path."""
    return Path(__file__).parent


def list_available_templates() -> list[str]:
    """
    Get list of available template names.

    Returns:
        List of template names
    """
    template_dir = get_template_dir()
    templates = []

    for item in template_dir.iterdir():
        if item.is_dir() and not item.name.startswith("_") and not item.name.startswith("."):
            templates.append(item.name)

    return sorted(templates)
