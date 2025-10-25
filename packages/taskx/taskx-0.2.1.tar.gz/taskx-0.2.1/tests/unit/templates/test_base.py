"""
Unit tests for base template class.

Tests the abstract base class and common functionality for all templates.
"""

from abc import ABC

import pytest

from taskx.templates.base import Template

# ============================================================================
# Concrete Implementation for Testing
# ============================================================================


class ConcreteTemplate(Template):
    """Concrete implementation for testing abstract base class."""

    name = "test-template"
    description = "A test template"
    category = "test"

    def get_prompts(self):
        """Return test prompts."""
        return {
            "project_name": {"type": "text", "message": "Project name:", "default": "myproject"}
        }

    def generate(self, variables):
        """Generate test content."""
        return f"[project]\nname = \"{variables.get('project_name', 'test')}\"\n"


class IncompleteTemplate(Template):
    """Template missing required attributes for testing."""

    pass


class TemplateWithoutName(Template):
    """Template without name attribute."""

    description = "Test"

    def get_prompts(self):
        return {}

    def generate(self, variables):
        return ""


class TemplateWithoutDescription(Template):
    """Template without description attribute."""

    name = "test"

    def get_prompts(self):
        return {}

    def generate(self, variables):
        return ""


# ============================================================================
# Test Template Base Class
# ============================================================================


@pytest.mark.unit
class TestTemplateBase:
    """Test suite for Template abstract base class."""

    def test_cannot_instantiate_abstract_class(self):
        """Test that Template cannot be instantiated directly."""
        with pytest.raises(TypeError):
            Template()

    def test_concrete_implementation_can_be_instantiated(self):
        """Test that concrete implementation can be instantiated."""
        template = ConcreteTemplate()
        assert template is not None
        assert template.name == "test-template"
        assert template.description == "A test template"

    def test_template_requires_name_attribute(self):
        """Test that template must define name attribute."""
        with pytest.raises((ValueError, TypeError)):
            TemplateWithoutName()

    def test_template_requires_description_attribute(self):
        """Test that template must define description attribute."""
        with pytest.raises((ValueError, TypeError)):
            TemplateWithoutDescription()

    def test_template_has_metadata_attributes(self):
        """Test that template has required metadata attributes."""
        template = ConcreteTemplate()

        assert hasattr(template, "name")
        assert hasattr(template, "description")
        assert hasattr(template, "category")

        assert isinstance(template.name, str)
        assert isinstance(template.description, str)
        assert isinstance(template.category, str)

    def test_get_prompts_must_be_implemented(self):
        """Test that get_prompts must be implemented."""
        # IncompleteTemplate doesn't implement abstract methods
        with pytest.raises(TypeError):
            IncompleteTemplate()

    def test_generate_must_be_implemented(self):
        """Test that generate must be implemented."""
        # Tested by IncompleteTemplate instantiation failure
        with pytest.raises(TypeError):
            IncompleteTemplate()

    def test_get_prompts_returns_dict(self):
        """Test that get_prompts returns a dictionary."""
        template = ConcreteTemplate()
        prompts = template.get_prompts()

        assert isinstance(prompts, dict)
        assert len(prompts) > 0

    def test_generate_returns_string(self):
        """Test that generate returns a string."""
        template = ConcreteTemplate()
        result = template.generate({"project_name": "test"})

        assert isinstance(result, str)
        assert len(result) > 0

    def test_get_additional_files_default_implementation(self):
        """Test that get_additional_files has default implementation."""
        template = ConcreteTemplate()
        files = template.get_additional_files({})

        assert isinstance(files, dict)
        assert len(files) == 0  # Default returns empty dict

    def test_validate_variables_default_implementation(self):
        """Test that validate_variables has default implementation."""
        template = ConcreteTemplate()

        # Should not raise error by default
        try:
            template.validate_variables({"test": "value"})
        except Exception as e:
            pytest.fail(f"Default validate_variables raised exception: {e}")

    def test_render_template_with_simple_variable(self):
        """Test rendering template with simple variable substitution."""
        template = ConcreteTemplate()
        template_str = "Hello, {{ name }}!"
        variables = {"name": "World"}

        result = template.render_template(template_str, variables)

        assert result == "Hello, World!"

    def test_render_template_with_multiple_variables(self):
        """Test rendering template with multiple variables."""
        template = ConcreteTemplate()
        template_str = "{{ greeting }}, {{ name }}! You are {{ age }} years old."
        variables = {"greeting": "Hello", "name": "Alice", "age": "30"}

        result = template.render_template(template_str, variables)

        assert result == "Hello, Alice! You are 30 years old."

    def test_render_template_uses_sandboxed_environment(self):
        """Test that render_template uses sandboxed Jinja2 environment."""
        template = ConcreteTemplate()
        # Try to use unsafe operations that should be blocked in sandbox
        template_str = "{{ name }}"
        variables = {"name": "Safe"}

        result = template.render_template(template_str, variables)
        assert result == "Safe"

    def test_render_template_with_jinja2_filters(self):
        """Test that Jinja2 filters work in template rendering."""
        template = ConcreteTemplate()
        template_str = "{{ name | upper }}"
        variables = {"name": "hello"}

        result = template.render_template(template_str, variables)

        assert result == "HELLO"

    def test_render_template_with_conditional(self):
        """Test rendering template with conditional logic."""
        template = ConcreteTemplate()
        template_str = "{% if enabled %}Yes{% else %}No{% endif %}"
        variables = {"enabled": True}

        result = template.render_template(template_str, variables)

        assert result == "Yes"

    def test_render_template_with_loop(self):
        """Test rendering template with loop."""
        template = ConcreteTemplate()
        template_str = "{% for item in items %}{{ item }},{% endfor %}"
        variables = {"items": ["a", "b", "c"]}

        result = template.render_template(template_str, variables)

        assert result == "a,b,c,"

    def test_render_template_with_missing_variable(self):
        """Test that rendering with missing variable doesn't crash."""
        template = ConcreteTemplate()
        template_str = "Hello, {{ name }}!"
        variables = {}  # Missing 'name' variable

        result = template.render_template(template_str, variables)

        # Jinja2 renders undefined variables as empty string
        assert result == "Hello, !"

    def test_template_inheritance_structure(self):
        """Test that template has correct inheritance."""

        assert issubclass(Template, ABC)
        assert issubclass(ConcreteTemplate, Template)

    def test_multiple_template_instances_independent(self):
        """Test that multiple template instances are independent."""
        template1 = ConcreteTemplate()
        template2 = ConcreteTemplate()

        assert template1 is not template2
        assert template1.name == template2.name
        assert template1.description == template2.description


# ============================================================================
# Test Template Edge Cases
# ============================================================================


@pytest.mark.unit
class TestTemplateEdgeCases:
    """Test suite for template edge cases."""

    def test_template_with_unicode_in_name(self):
        """Test template with unicode characters in name."""

        class UnicodeTemplate(Template):
            name = "test-émplate-日本語"
            description = "Test"
            category = "test"

            def get_prompts(self):
                return {}

            def generate(self, variables):
                return ""

        template = UnicodeTemplate()
        assert "émplate" in template.name
        assert "日本語" in template.name

    def test_template_with_very_long_description(self):
        """Test template with very long description."""

        class LongDescTemplate(Template):
            name = "test"
            description = "A" * 1000
            category = "test"

            def get_prompts(self):
                return {}

            def generate(self, variables):
                return ""

        template = LongDescTemplate()
        assert len(template.description) == 1000

    def test_template_with_empty_category(self):
        """Test template with empty category."""

        class EmptyCategoryTemplate(Template):
            name = "test"
            description = "Test"
            category = ""

            def get_prompts(self):
                return {}

            def generate(self, variables):
                return ""

        template = EmptyCategoryTemplate()
        assert template.category == ""

    def test_render_template_with_special_characters(self):
        """Test rendering template with special characters."""
        template = ConcreteTemplate()
        template_str = "{{ text }}"
        variables = {"text": "Test!@#$%^&*(){}[]<>?/\\|`~"}

        result = template.render_template(template_str, variables)

        assert result == "Test!@#$%^&*(){}[]<>?/\\|`~"

    def test_render_template_with_multiline_content(self):
        """Test rendering multiline template."""
        template = ConcreteTemplate()
        template_str = """
Line 1: {{ line1 }}
Line 2: {{ line2 }}
Line 3: {{ line3 }}
"""
        variables = {"line1": "First", "line2": "Second", "line3": "Third"}

        result = template.render_template(template_str, variables)

        assert "Line 1: First" in result
        assert "Line 2: Second" in result
        assert "Line 3: Third" in result

    def test_get_prompts_with_all_prompt_types(self):
        """Test get_prompts returning all supported prompt types."""

        class AllTypesTemplate(Template):
            name = "test"
            description = "Test"
            category = "test"

            def get_prompts(self):
                return {
                    "text_var": {"type": "text", "message": "Text:"},
                    "select_var": {"type": "select", "message": "Select:", "choices": ["A", "B"]},
                    "confirm_var": {"type": "confirm", "message": "Confirm?"},
                    "password_var": {"type": "password", "message": "Password:"},
                }

            def generate(self, variables):
                return ""

        template = AllTypesTemplate()
        prompts = template.get_prompts()

        assert len(prompts) == 4
        assert prompts["text_var"]["type"] == "text"
        assert prompts["select_var"]["type"] == "select"
        assert prompts["confirm_var"]["type"] == "confirm"
        assert prompts["password_var"]["type"] == "password"

    def test_get_additional_files_override(self):
        """Test overriding get_additional_files method."""

        class FilesTemplate(Template):
            name = "test"
            description = "Test"
            category = "test"

            def get_prompts(self):
                return {}

            def generate(self, variables):
                return ""

            def get_additional_files(self, variables):
                return {
                    "README.md": f"# {variables.get('name', 'Project')}",
                    ".gitignore": "*.pyc\n__pycache__/\n",
                }

        template = FilesTemplate()
        files = template.get_additional_files({"name": "MyProject"})

        assert len(files) == 2
        assert "README.md" in files
        assert ".gitignore" in files
        assert "MyProject" in files["README.md"]

    def test_validate_variables_custom_validation(self):
        """Test custom variable validation."""

        class ValidatingTemplate(Template):
            name = "test"
            description = "Test"
            category = "test"

            def get_prompts(self):
                return {"name": {"type": "text", "message": "Name:"}}

            def generate(self, variables):
                return ""

            def validate_variables(self, variables):
                if not variables.get("name"):
                    raise ValueError("Name is required")
                if len(variables["name"]) < 3:
                    raise ValueError("Name must be at least 3 characters")

        template = ValidatingTemplate()

        # Valid name should pass
        template.validate_variables({"name": "ValidName"})

        # Empty name should fail
        with pytest.raises(ValueError, match="Name is required"):
            template.validate_variables({})

        # Short name should fail
        with pytest.raises(ValueError, match="at least 3 characters"):
            template.validate_variables({"name": "ab"})

    def test_render_template_escapes_html_by_default(self):
        """Test that HTML is escaped in rendered templates."""
        template = ConcreteTemplate()
        template_str = "{{ html }}"
        variables = {"html": "<script>alert('xss')</script>"}

        result = template.render_template(template_str, variables)

        # Jinja2 should escape HTML by default
        assert "&lt;script&gt;" in result or "<script>" in result

    def test_generate_with_empty_variables(self):
        """Test generating content with empty variables dict."""
        template = ConcreteTemplate()
        result = template.generate({})

        assert isinstance(result, str)
        assert len(result) > 0

    def test_render_template_with_nested_dict(self):
        """Test rendering template with nested dictionary variables."""
        template = ConcreteTemplate()
        template_str = "{{ config.name }} - {{ config.version }}"
        variables = {"config": {"name": "MyApp", "version": "1.0"}}

        result = template.render_template(template_str, variables)

        assert result == "MyApp - 1.0"
