"""
Unit tests for interactive prompts.

Tests prompt configuration, validation, and execution in both interactive and non-interactive modes.
"""

from unittest.mock import patch

import pytest

from taskx.core.prompts import (
    ConfirmConfig,
    PromptConfig,
    PromptManager,
    parse_confirm_config,
    parse_prompt_config,
)

# ============================================================================
# Test PromptConfig
# ============================================================================


@pytest.mark.unit
class TestPromptConfig:
    """Test suite for PromptConfig dataclass."""

    def test_valid_text_prompt(self):
        """Test creating a valid text prompt."""
        config = PromptConfig(type="text", message="Enter your name:")
        assert config.type == "text"
        assert config.message == "Enter your name:"
        assert config.choices is None
        assert config.default is None

    def test_valid_select_prompt(self):
        """Test creating a valid select prompt."""
        config = PromptConfig(
            type="select", message="Choose an option:", choices=["A", "B", "C"], default="A"
        )
        assert config.type == "select"
        assert config.choices == ["A", "B", "C"]
        assert config.default == "A"

    def test_valid_confirm_prompt(self):
        """Test creating a valid confirm prompt."""
        config = PromptConfig(type="confirm", message="Continue?", default=True)
        assert config.type == "confirm"
        assert config.default is True

    def test_valid_password_prompt(self):
        """Test creating a valid password prompt."""
        config = PromptConfig(type="password", message="Enter password:")
        assert config.type == "password"

    def test_invalid_prompt_type_raises_error(self):
        """Test that invalid prompt type raises ValueError."""
        with pytest.raises(ValueError, match="Invalid prompt type"):
            PromptConfig(type="invalid", message="Test")

    def test_select_without_choices_raises_error(self):
        """Test that select prompt without choices raises ValueError."""
        with pytest.raises(ValueError, match="Select prompt requires 'choices'"):
            PromptConfig(type="select", message="Choose:")

    def test_prompt_with_default_value(self):
        """Test prompt with default value."""
        config = PromptConfig(type="text", message="Name:", default="John")
        assert config.default == "John"

    def test_prompt_with_validation_regex(self):
        """Test prompt with validation regex."""
        config = PromptConfig(type="text", message="Email:", validate=r"^[\w\.-]+@[\w\.-]+\.\w+$")
        assert config.validate == r"^[\w\.-]+@[\w\.-]+\.\w+$"

    @pytest.mark.parametrize("prompt_type", ["text", "select", "confirm", "password"])
    def test_all_valid_prompt_types(self, prompt_type):
        """Test that all valid prompt types are accepted."""
        kwargs = {"type": prompt_type, "message": "Test"}
        if prompt_type == "select":
            kwargs["choices"] = ["A", "B"]

        config = PromptConfig(**kwargs)
        assert config.type == prompt_type


# ============================================================================
# Test ConfirmConfig
# ============================================================================


@pytest.mark.unit
class TestConfirmConfig:
    """Test suite for ConfirmConfig dataclass."""

    def test_confirm_config_with_message(self):
        """Test creating confirm config with message."""
        config = ConfirmConfig(message="Are you sure?")
        assert config.message == "Are you sure?"
        assert config.default is False

    def test_confirm_config_with_default_true(self):
        """Test confirm config with default True."""
        config = ConfirmConfig(message="Continue?", default=True)
        assert config.default is True

    def test_confirm_config_with_default_false(self):
        """Test confirm config with default False."""
        config = ConfirmConfig(message="Continue?", default=False)
        assert config.default is False


# ============================================================================
# Test PromptManager - Interactive Mode
# ============================================================================


@pytest.mark.unit
class TestPromptManagerInteractive:
    """Test suite for PromptManager in interactive mode."""

    def test_prompt_manager_detects_interactive_mode(self, mock_isatty):
        """Test that PromptManager detects interactive mode."""
        manager = PromptManager()
        assert manager.is_interactive is True

    def test_prompt_manager_detects_non_interactive_mode(self, non_interactive_env):
        """Test that PromptManager detects non-interactive mode."""
        manager = PromptManager()
        assert manager.is_interactive is False

    @patch("questionary.text")
    def test_text_prompt_in_interactive_mode(self, mock_text, interactive_env):
        """Test text prompt in interactive mode."""
        mock_text.return_value.ask.return_value = "John Doe"

        manager = PromptManager()
        prompts = {"NAME": PromptConfig(type="text", message="Enter your name:")}

        result = manager.prompt_for_variables(prompts)

        assert result == {"NAME": "John Doe"}
        mock_text.assert_called_once()

    @patch("questionary.select")
    def test_select_prompt_in_interactive_mode(self, mock_select, interactive_env):
        """Test select prompt in interactive mode."""
        mock_select.return_value.ask.return_value = "production"

        manager = PromptManager()
        prompts = {
            "ENV": PromptConfig(
                type="select",
                message="Choose environment:",
                choices=["dev", "staging", "production"],
            )
        }

        result = manager.prompt_for_variables(prompts)

        assert result == {"ENV": "production"}
        mock_select.assert_called_once()

    @patch("questionary.confirm")
    def test_confirm_prompt_in_interactive_mode(self, mock_confirm, interactive_env):
        """Test confirm prompt in interactive mode."""
        mock_confirm.return_value.ask.return_value = True

        manager = PromptManager()
        prompts = {"PROCEED": PromptConfig(type="confirm", message="Continue?")}

        result = manager.prompt_for_variables(prompts)

        assert result == {"PROCEED": "True"}
        mock_confirm.assert_called_once()

    @patch("questionary.password")
    def test_password_prompt_in_interactive_mode(self, mock_password, interactive_env):
        """Test password prompt in interactive mode."""
        mock_password.return_value.ask.return_value = "secret123"

        manager = PromptManager()
        prompts = {"PASSWORD": PromptConfig(type="password", message="Enter password:")}

        result = manager.prompt_for_variables(prompts)

        assert result == {"PASSWORD": "secret123"}
        mock_password.assert_called_once()

    @patch("questionary.text")
    def test_prompt_with_default_value(self, mock_text, interactive_env):
        """Test prompt with default value."""
        mock_text.return_value.ask.return_value = "Custom Value"

        manager = PromptManager()
        prompts = {"NAME": PromptConfig(type="text", message="Name:", default="Default")}

        result = manager.prompt_for_variables(prompts)

        assert result == {"NAME": "Custom Value"}
        # Verify default was passed to questionary
        call_args = mock_text.call_args
        assert call_args[1]["default"] == "Default"

    @patch("questionary.text")
    def test_keyboard_interrupt_raises_exception(self, mock_text, interactive_env):
        """Test that KeyboardInterrupt during prompt is handled."""
        mock_text.return_value.ask.side_effect = KeyboardInterrupt()

        manager = PromptManager()
        prompts = {"NAME": PromptConfig(type="text", message="Enter name:")}

        with pytest.raises(KeyboardInterrupt):
            manager.prompt_for_variables(prompts)

    @patch("questionary.text")
    def test_multiple_prompts_in_sequence(self, mock_text, interactive_env):
        """Test multiple prompts are asked in sequence."""
        mock_text.return_value.ask.side_effect = ["Value1", "Value2", "Value3"]

        manager = PromptManager()
        prompts = {
            "VAR1": PromptConfig(type="text", message="First:"),
            "VAR2": PromptConfig(type="text", message="Second:"),
            "VAR3": PromptConfig(type="text", message="Third:"),
        }

        result = manager.prompt_for_variables(prompts)

        assert result == {"VAR1": "Value1", "VAR2": "Value2", "VAR3": "Value3"}
        assert mock_text.call_count == 3


# ============================================================================
# Test PromptManager - Non-Interactive Mode
# ============================================================================


@pytest.mark.unit
class TestPromptManagerNonInteractive:
    """Test suite for PromptManager in non-interactive mode."""

    def test_non_interactive_uses_default_value(self, non_interactive_env):
        """Test that non-interactive mode uses default values."""
        manager = PromptManager()
        prompts = {"NAME": PromptConfig(type="text", message="Name:", default="DefaultName")}

        result = manager.prompt_for_variables(prompts)

        assert result == {"NAME": "DefaultName"}

    def test_non_interactive_without_default_raises_error(self, non_interactive_env):
        """Test that non-interactive mode without default raises error."""
        manager = PromptManager()
        prompts = {"NAME": PromptConfig(type="text", message="Name:")}

        with pytest.raises(RuntimeError, match="Cannot prompt for 'NAME'"):
            manager.prompt_for_variables(prompts)

    def test_non_interactive_with_env_override(self, non_interactive_env):
        """Test that env overrides work in non-interactive mode."""
        manager = PromptManager()
        prompts = {"NAME": PromptConfig(type="text", message="Name:")}

        result = manager.prompt_for_variables(prompts, env_overrides={"NAME": "OverriddenName"})

        assert result == {"NAME": "OverriddenName"}

    def test_env_override_takes_precedence_over_default(self, non_interactive_env):
        """Test that env overrides take precedence over defaults."""
        manager = PromptManager()
        prompts = {"NAME": PromptConfig(type="text", message="Name:", default="Default")}

        result = manager.prompt_for_variables(prompts, env_overrides={"NAME": "Override"})

        assert result == {"NAME": "Override"}

    def test_env_override_in_interactive_mode(self, interactive_env):
        """Test that env overrides work in interactive mode too."""
        manager = PromptManager()
        prompts = {"NAME": PromptConfig(type="text", message="Name:")}

        result = manager.prompt_for_variables(prompts, env_overrides={"NAME": "Override"})

        # Should use override without prompting
        assert result == {"NAME": "Override"}


# ============================================================================
# Test PromptManager - Confirmation
# ============================================================================


@pytest.mark.unit
class TestPromptManagerConfirmation:
    """Test suite for confirmation prompts."""

    @patch("questionary.confirm")
    def test_confirm_action_returns_true(self, mock_confirm, interactive_env):
        """Test that confirmation returns True when user confirms."""
        mock_confirm.return_value.ask.return_value = True

        manager = PromptManager()
        result = manager.confirm_action("Are you sure?")

        assert result is True

    @patch("questionary.confirm")
    def test_confirm_action_returns_false(self, mock_confirm, interactive_env):
        """Test that confirmation returns False when user declines."""
        mock_confirm.return_value.ask.return_value = False

        manager = PromptManager()
        result = manager.confirm_action("Are you sure?")

        assert result is False

    @patch("questionary.confirm")
    def test_confirm_action_with_custom_default(self, mock_confirm, interactive_env):
        """Test confirmation with custom default value."""
        mock_confirm.return_value.ask.return_value = True

        manager = PromptManager()
        result = manager.confirm_action("Proceed?", default=True)

        assert result is True
        # Verify default was passed
        call_args = mock_confirm.call_args
        assert call_args[1]["default"] is True

    def test_confirm_action_with_force_flag(self, interactive_env):
        """Test that force flag skips confirmation."""
        manager = PromptManager()
        result = manager.confirm_action("Are you sure?", force=True)

        # Should return True without prompting
        assert result is True

    def test_confirm_action_non_interactive_uses_default(self, non_interactive_env):
        """Test that non-interactive mode uses default for confirmation."""
        manager = PromptManager()
        result = manager.confirm_action("Proceed?", default=True)

        assert result is True

    @patch("questionary.confirm")
    def test_confirm_action_handles_keyboard_interrupt(self, mock_confirm, interactive_env):
        """Test that KeyboardInterrupt during confirmation returns False."""
        mock_confirm.return_value.ask.side_effect = KeyboardInterrupt()

        manager = PromptManager()
        result = manager.confirm_action("Proceed?")

        assert result is False

    @patch("questionary.confirm")
    def test_confirm_action_handles_none_response(self, mock_confirm, interactive_env):
        """Test that None response returns False (user cancelled)."""
        mock_confirm.return_value.ask.return_value = None

        manager = PromptManager()

        result = manager.confirm_action("Proceed?")
        assert result is False


# ============================================================================
# Test PromptManager - Select from List
# ============================================================================


@pytest.mark.unit
class TestPromptManagerSelectFromList:
    """Test suite for select from list functionality."""

    @patch("questionary.select")
    def test_select_from_list_returns_choice(self, mock_select, interactive_env):
        """Test selecting from a list."""
        mock_select.return_value.ask.return_value = "Option B"

        manager = PromptManager()
        result = manager.select_from_list("Choose:", choices=["Option A", "Option B", "Option C"])

        assert result == "Option B"

    @patch("questionary.select")
    def test_select_from_list_with_default(self, mock_select, interactive_env):
        """Test selecting from list with default value."""
        mock_select.return_value.ask.return_value = "Default"

        manager = PromptManager()
        result = manager.select_from_list(
            "Choose:", choices=["A", "B", "Default"], default="Default"
        )

        assert result == "Default"

    def test_select_from_list_non_interactive(self, non_interactive_env):
        """Test select from list in non-interactive mode."""
        manager = PromptManager()
        result = manager.select_from_list("Choose:", choices=["A", "B", "C"], default="B")

        # Should return default without prompting
        assert result == "B"

    @patch("questionary.select")
    def test_select_from_list_handles_keyboard_interrupt(self, mock_select, interactive_env):
        """Test that KeyboardInterrupt returns None."""
        mock_select.return_value.ask.side_effect = KeyboardInterrupt()

        manager = PromptManager()
        result = manager.select_from_list("Choose:", choices=["A", "B"])

        assert result is None


# ============================================================================
# Test parse_prompt_config
# ============================================================================


@pytest.mark.unit
class TestParsePromptConfig:
    """Test suite for parse_prompt_config function."""

    def test_parse_simple_string_prompt(self):
        """Test parsing simple string prompt."""
        config_dict = {"NAME": "Enter your name:"}

        result = parse_prompt_config(config_dict)

        assert "NAME" in result
        assert result["NAME"].type == "text"
        assert result["NAME"].message == "Enter your name:"

    def test_parse_full_text_prompt_config(self):
        """Test parsing full text prompt configuration."""
        config_dict = {"NAME": {"type": "text", "message": "Enter your name:", "default": "John"}}

        result = parse_prompt_config(config_dict)

        assert result["NAME"].type == "text"
        assert result["NAME"].message == "Enter your name:"
        assert result["NAME"].default == "John"

    def test_parse_select_prompt_config(self):
        """Test parsing select prompt configuration."""
        config_dict = {
            "ENV": {
                "type": "select",
                "message": "Choose environment:",
                "choices": ["dev", "staging", "prod"],
                "default": "dev",
            }
        }

        result = parse_prompt_config(config_dict)

        assert result["ENV"].type == "select"
        assert result["ENV"].choices == ["dev", "staging", "prod"]
        assert result["ENV"].default == "dev"

    def test_parse_confirm_prompt_config(self):
        """Test parsing confirm prompt configuration."""
        config_dict = {"PROCEED": {"type": "confirm", "message": "Continue?", "default": True}}

        result = parse_prompt_config(config_dict)

        assert result["PROCEED"].type == "confirm"
        assert result["PROCEED"].default is True

    def test_parse_password_prompt_config(self):
        """Test parsing password prompt configuration."""
        config_dict = {"PASSWORD": {"type": "password", "message": "Enter password:"}}

        result = parse_prompt_config(config_dict)

        assert result["PASSWORD"].type == "password"

    def test_parse_multiple_prompts(self):
        """Test parsing multiple prompts."""
        config_dict = {
            "NAME": "Enter name:",
            "AGE": {"type": "text", "message": "Enter age:"},
            "ENV": {"type": "select", "choices": ["dev", "prod"]},
        }

        result = parse_prompt_config(config_dict)

        assert len(result) == 3
        assert "NAME" in result
        assert "AGE" in result
        assert "ENV" in result

    def test_parse_prompt_with_default_message(self):
        """Test that default message is generated when not provided."""
        config_dict = {"API_KEY": {"type": "text"}}

        result = parse_prompt_config(config_dict)

        # Should generate default message
        assert "API_KEY" in result["API_KEY"].message

    def test_parse_prompt_defaults_to_text_type(self):
        """Test that prompt type defaults to 'text' when not specified."""
        config_dict = {"NAME": {"message": "Enter name:"}}

        result = parse_prompt_config(config_dict)

        assert result["NAME"].type == "text"

    def test_parse_invalid_prompt_type_raises_error(self):
        """Test that invalid prompt configuration raises error."""
        config_dict = {"NAME": 123}  # Invalid: not string or dict

        with pytest.raises(ValueError, match="Invalid prompt configuration"):
            parse_prompt_config(config_dict)

    def test_parse_empty_config_dict(self):
        """Test parsing empty configuration dictionary."""
        result = parse_prompt_config({})

        assert result == {}


# ============================================================================
# Test parse_confirm_config
# ============================================================================


@pytest.mark.unit
class TestParseConfirmConfig:
    """Test suite for parse_confirm_config function."""

    def test_parse_confirm_true(self):
        """Test parsing True value."""
        result = parse_confirm_config(True)

        assert result is not None
        assert result.message == "Continue?"
        assert result.default is False

    def test_parse_confirm_false_returns_none(self):
        """Test parsing False value returns None."""
        result = parse_confirm_config(False)

        assert result is None

    def test_parse_confirm_none_returns_none(self):
        """Test parsing None value returns None."""
        result = parse_confirm_config(None)

        assert result is None

    def test_parse_confirm_string(self):
        """Test parsing string confirmation message."""
        result = parse_confirm_config("Are you sure you want to deploy?")

        assert result is not None
        assert result.message == "Are you sure you want to deploy?"
        assert result.default is False

    def test_parse_confirm_dict(self):
        """Test parsing dict configuration."""
        result = parse_confirm_config({"message": "Deploy to production?", "default": True})

        assert result is not None
        assert result.message == "Deploy to production?"
        assert result.default is True

    def test_parse_confirm_dict_with_defaults(self):
        """Test parsing dict with default values."""
        result = parse_confirm_config({})

        assert result is not None
        assert result.message == "Continue?"
        assert result.default is False

    def test_parse_confirm_invalid_type_raises_error(self):
        """Test that invalid type raises ValueError."""
        with pytest.raises(ValueError, match="Invalid confirm configuration"):
            parse_confirm_config(123)


# ============================================================================
# Test Edge Cases and Error Handling
# ============================================================================


@pytest.mark.unit
class TestPromptEdgeCases:
    """Test suite for edge cases and error handling."""

    def test_empty_prompt_message(self):
        """Test prompt with empty message."""
        config = PromptConfig(type="text", message="")
        assert config.message == ""

    def test_very_long_prompt_message(self):
        """Test prompt with very long message."""
        long_message = "A" * 1000
        config = PromptConfig(type="text", message=long_message)
        assert len(config.message) == 1000

    def test_select_prompt_with_many_choices(self):
        """Test select prompt with many choices."""
        choices = [f"Choice {i}" for i in range(100)]
        config = PromptConfig(type="select", message="Choose:", choices=choices)
        assert len(config.choices) == 100

    def test_prompt_with_unicode_characters(self):
        """Test prompt with unicode characters."""
        config = PromptConfig(type="text", message="Enter your name: 你好 👋")
        assert "你好" in config.message
        assert "👋" in config.message

    def test_prompt_with_special_characters(self):
        """Test prompt with special characters."""
        config = PromptConfig(type="text", message="Enter value (e.g., test@example.com):")
        assert "@" in config.message
        assert "(" in config.message

    def test_default_value_type_preservation(self):
        """Test that default value types are preserved."""
        text_config = PromptConfig(type="text", message="Text:", default="string")
        confirm_config = PromptConfig(type="confirm", message="Confirm:", default=True)

        assert isinstance(text_config.default, str)
        assert isinstance(confirm_config.default, bool)

    @patch("questionary.text")
    def test_prompt_return_value_conversion_to_string(self, mock_text, interactive_env):
        """Test that all prompt return values are converted to strings."""
        mock_text.return_value.ask.return_value = 42  # Return integer

        manager = PromptManager()
        prompts = {"VALUE": PromptConfig(type="text", message="Enter:")}

        result = manager.prompt_for_variables(prompts)

        # Should be converted to string
        assert result["VALUE"] == "42"
        assert isinstance(result["VALUE"], str)

    def test_multiple_prompts_with_mixed_types(self):
        """Test multiple prompts with different types."""
        config_dict = {
            "NAME": {"type": "text", "message": "Name:"},
            "ENV": {"type": "select", "message": "Env:", "choices": ["dev", "prod"]},
            "CONFIRM": {"type": "confirm", "message": "OK?"},
            "PASSWORD": {"type": "password", "message": "Pass:"},
        }

        result = parse_prompt_config(config_dict)

        assert len(result) == 4
        assert result["NAME"].type == "text"
        assert result["ENV"].type == "select"
        assert result["CONFIRM"].type == "confirm"
        assert result["PASSWORD"].type == "password"
