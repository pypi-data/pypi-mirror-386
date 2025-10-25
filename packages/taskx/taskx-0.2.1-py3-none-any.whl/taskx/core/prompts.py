"""
Interactive prompt management for taskx.

Provides user input prompts during task execution using questionary.

Copyright (c) 2025 taskx Project
Licensed under Proprietary License - See LICENSE file
"""

import sys
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union

import questionary


@dataclass
class PromptConfig:
    """Configuration for an interactive prompt."""

    type: str  # "text", "select", "confirm", "password"
    message: str
    choices: Optional[List[str]] = None
    default: Optional[Union[str, bool]] = None
    validate: Optional[str] = None  # Validation regex pattern

    def __post_init__(self) -> None:
        """Validate prompt configuration."""
        valid_types = {"text", "select", "confirm", "password"}
        if self.type not in valid_types:
            raise ValueError(
                f"Invalid prompt type '{self.type}'. " f"Must be one of: {', '.join(valid_types)}"
            )

        if self.type == "select" and not self.choices:
            raise ValueError("Select prompt requires 'choices' field")


@dataclass
class ConfirmConfig:
    """Configuration for a confirmation prompt."""

    message: str
    default: bool = False


class PromptManager:
    """Manages interactive prompts for task execution."""

    def __init__(self) -> None:
        """Initialize prompt manager."""
        self.is_interactive = sys.stdin.isatty() and sys.stdout.isatty()

    def prompt_for_variables(
        self, prompts: Dict[str, PromptConfig], env_overrides: Optional[Dict[str, str]] = None
    ) -> Dict[str, str]:
        """
        Prompt user for variable values.

        Args:
            prompts: Dictionary of variable names to prompt configurations
            env_overrides: Optional environment variable overrides from CLI

        Returns:
            Dictionary of variable names to user-provided values

        Raises:
            RuntimeError: If running in non-interactive mode without defaults
            KeyboardInterrupt: If user cancels prompt
        """
        if env_overrides is None:
            env_overrides = {}

        results = {}

        for var_name, prompt_config in prompts.items():
            # Check if value provided via env override
            if var_name in env_overrides:
                results[var_name] = env_overrides[var_name]
                continue

            # Check if running in non-interactive environment
            if not self.is_interactive:
                if prompt_config.default is not None:
                    results[var_name] = str(prompt_config.default)
                else:
                    raise RuntimeError(
                        f"Cannot prompt for '{var_name}' in non-interactive mode. "
                        f"Provide value via --env {var_name}=VALUE or set a default value"
                    )
                continue

            # Interactive prompt
            value = self._prompt_user(var_name, prompt_config)
            if value is None:
                raise KeyboardInterrupt("User cancelled prompt")

            results[var_name] = str(value)

        return results

    def _prompt_user(self, var_name: str, config: PromptConfig) -> Any:
        """
        Prompt user for a single variable value.

        Args:
            var_name: Variable name
            config: Prompt configuration

        Returns:
            User-provided value
        """
        try:
            if config.type == "select":
                return questionary.select(
                    message=config.message, choices=config.choices, default=config.default
                ).ask()

            elif config.type == "text":
                return questionary.text(
                    message=config.message, default=str(config.default) if config.default else ""
                ).ask()

            elif config.type == "password":
                return questionary.password(message=config.message).ask()

            elif config.type == "confirm":
                default_val = bool(config.default) if config.default is not None else False
                return questionary.confirm(message=config.message, default=default_val).ask()

            else:
                raise ValueError(f"Unsupported prompt type: {config.type}")

        except KeyboardInterrupt:
            return None

    def confirm_action(self, message: str, default: bool = False, force: bool = False) -> bool:
        """
        Ask user for confirmation.

        Args:
            message: Confirmation message
            default: Default value if user just presses Enter
            force: If True, skip prompt and return True (for automation)

        Returns:
            True if user confirmed, False otherwise

        Raises:
            KeyboardInterrupt: If user cancels
        """
        # Skip prompt if force flag is set
        if force:
            return True

        # In non-interactive mode, use default
        if not self.is_interactive:
            return default

        try:
            result = questionary.confirm(message=message, default=default).ask()
            if result is None:
                raise KeyboardInterrupt("User cancelled confirmation")
            return result
        except KeyboardInterrupt:
            return False

    def select_from_list(
        self, message: str, choices: List[str], default: Optional[str] = None
    ) -> Optional[str]:
        """
        Prompt user to select from a list of choices.

        Args:
            message: Prompt message
            choices: List of available choices
            default: Default selection

        Returns:
            Selected choice or None if cancelled
        """
        if not self.is_interactive:
            return default

        try:
            return questionary.select(message=message, choices=choices, default=default).ask()
        except KeyboardInterrupt:
            return None


def parse_prompt_config(config_dict: Dict[str, Any]) -> Dict[str, PromptConfig]:
    """
    Parse prompt configuration from task definition.

    Args:
        config_dict: Raw prompt configuration dictionary

    Returns:
        Dictionary of variable names to PromptConfig objects

    Raises:
        ValueError: If configuration is invalid
    """
    prompts = {}

    for var_name, prompt_def in config_dict.items():
        if isinstance(prompt_def, str):
            # Simple string prompt defaults to text input
            prompts[var_name] = PromptConfig(type="text", message=prompt_def)
        elif isinstance(prompt_def, dict):
            # Full prompt configuration
            prompt_type = prompt_def.get("type", "text")
            message = prompt_def.get("message", f"Enter value for {var_name}:")
            choices = prompt_def.get("choices")
            default = prompt_def.get("default")
            validate = prompt_def.get("validate")

            prompts[var_name] = PromptConfig(
                type=prompt_type,
                message=message,
                choices=choices,
                default=default,
                validate=validate,
            )
        else:
            raise ValueError(
                f"Invalid prompt configuration for '{var_name}': "
                f"must be string or dict, got {type(prompt_def)}"
            )

    return prompts


def parse_confirm_config(config: Union[str, Dict[str, Any], bool]) -> Optional[ConfirmConfig]:
    """
    Parse confirmation configuration.

    Args:
        config: Confirmation configuration (string, dict, or bool)

    Returns:
        ConfirmConfig object or None if confirmation not needed
    """
    if config is None or config is False:
        return None

    if config is True:
        # Simple True means confirm with default message
        return ConfirmConfig(message="Continue?", default=False)

    if isinstance(config, str):
        # String is the confirmation message
        return ConfirmConfig(message=config, default=False)

    if isinstance(config, dict):
        # Full configuration
        message = config.get("message", "Continue?")
        default = config.get("default", False)
        return ConfirmConfig(message=message, default=default)

    raise ValueError(f"Invalid confirm configuration: {config}")
