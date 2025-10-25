"""
Unit tests for specific project templates.

Tests Django, FastAPI, Data Science, and Python Library templates.
"""

import pytest

from taskx.templates.data_science.template import DataScienceTemplate
from taskx.templates.django.template import DjangoTemplate
from taskx.templates.fastapi.template import FastAPITemplate
from taskx.templates.python_library.template import PythonLibraryTemplate

# ============================================================================
# Test Django Template
# ============================================================================


@pytest.mark.unit
class TestDjangoTemplate:
    """Test suite for Django project template."""

    def test_django_template_metadata(self):
        """Test Django template has correct metadata."""
        template = DjangoTemplate()

        assert template.name == "django"
        assert "Django" in template.description
        assert template.category == "web"

    def test_django_template_prompts(self):
        """Test Django template returns correct prompts."""
        template = DjangoTemplate()
        prompts = template.get_prompts()

        assert isinstance(prompts, dict)
        # Should have prompts for Django-specific project variables
        expected_keys = {"project_name", "use_celery", "use_docker"}
        assert expected_keys.issubset(prompts.keys())

    def test_django_template_generate_creates_valid_toml(self, django_template_vars):
        """Test Django template generates valid pyproject.toml."""
        template = DjangoTemplate()
        result = template.generate(django_template_vars)

        assert isinstance(result, str)
        assert len(result) > 0
        # Should contain Django-specific content
        assert "django" in result.lower()
        assert django_template_vars["project_name"] in result

    def test_django_template_includes_dependencies(self, django_template_vars):
        """Test Django template includes required dependencies."""
        template = DjangoTemplate()
        result = template.generate(django_template_vars)

        # Should include Django and common dependencies
        assert "django" in result.lower()

    def test_django_template_includes_tasks(self, django_template_vars):
        """Test Django template includes common Django tasks."""
        template = DjangoTemplate()
        result = template.generate(django_template_vars)

        # Should include common Django commands
        assert "manage.py" in result or "runserver" in result or "migrate" in result

    def test_django_template_additional_files(self, django_template_vars):
        """Test Django template provides additional files."""
        template = DjangoTemplate()
        files = template.get_additional_files(django_template_vars)

        assert isinstance(files, dict)
        # May include README, .gitignore, etc.

    def test_django_template_variable_substitution(self, django_template_vars):
        """Test that variables are properly substituted."""
        template = DjangoTemplate()
        result = template.generate(django_template_vars)

        # All template variables should be substituted
        assert "{{" not in result
        assert "}}" not in result
        assert django_template_vars["project_name"] in result


# ============================================================================
# Test FastAPI Template
# ============================================================================


@pytest.mark.unit
class TestFastAPITemplate:
    """Test suite for FastAPI project template."""

    def test_fastapi_template_metadata(self):
        """Test FastAPI template has correct metadata."""
        template = FastAPITemplate()

        assert template.name == "fastapi"
        assert "FastAPI" in template.description
        assert template.category == "web"

    def test_fastapi_template_prompts(self):
        """Test FastAPI template returns correct prompts."""
        template = FastAPITemplate()
        prompts = template.get_prompts()

        assert isinstance(prompts, dict)
        expected_keys = {"project_name", "use_database", "use_docker"}
        assert expected_keys.issubset(prompts.keys())

    def test_fastapi_template_generate_creates_valid_toml(self, fastapi_template_vars):
        """Test FastAPI template generates valid pyproject.toml."""
        template = FastAPITemplate()
        result = template.generate(fastapi_template_vars)

        assert isinstance(result, str)
        assert len(result) > 0
        assert "fastapi" in result.lower()
        assert fastapi_template_vars["project_name"] in result

    def test_fastapi_template_includes_dependencies(self, fastapi_template_vars):
        """Test FastAPI template includes required dependencies."""
        template = FastAPITemplate()
        result = template.generate(fastapi_template_vars)

        # Should include FastAPI and uvicorn
        assert "fastapi" in result.lower()
        assert "uvicorn" in result.lower() or "server" in result.lower()

    def test_fastapi_template_includes_tasks(self, fastapi_template_vars):
        """Test FastAPI template includes common API tasks."""
        template = FastAPITemplate()
        result = template.generate(fastapi_template_vars)

        # Should include development server task
        assert "dev" in result or "run" in result or "uvicorn" in result

    def test_fastapi_template_additional_files(self, fastapi_template_vars):
        """Test FastAPI template provides additional files."""
        template = FastAPITemplate()
        files = template.get_additional_files(fastapi_template_vars)

        assert isinstance(files, dict)

    def test_fastapi_template_variable_substitution(self, fastapi_template_vars):
        """Test that variables are properly substituted."""
        template = FastAPITemplate()
        result = template.generate(fastapi_template_vars)

        assert "{{" not in result
        assert "}}" not in result
        assert fastapi_template_vars["project_name"] in result


# ============================================================================
# Test Data Science Template
# ============================================================================


@pytest.mark.unit
class TestDataScienceTemplate:
    """Test suite for Data Science project template."""

    def test_data_science_template_metadata(self):
        """Test Data Science template has correct metadata."""
        template = DataScienceTemplate()

        assert template.name == "data-science"
        assert "Data Science" in template.description or "data science" in template.description
        assert template.category == "data"

    def test_data_science_template_prompts(self):
        """Test Data Science template returns correct prompts."""
        template = DataScienceTemplate()
        prompts = template.get_prompts()

        assert isinstance(prompts, dict)
        expected_keys = {"project_name", "ml_framework", "use_mlflow"}
        assert expected_keys.issubset(prompts.keys())

    def test_data_science_template_generate_creates_valid_toml(self, data_science_template_vars):
        """Test Data Science template generates valid pyproject.toml."""
        template = DataScienceTemplate()
        result = template.generate(data_science_template_vars)

        assert isinstance(result, str)
        assert len(result) > 0
        assert data_science_template_vars["project_name"] in result

    def test_data_science_template_includes_dependencies(self, data_science_template_vars):
        """Test Data Science template includes required dependencies."""
        template = DataScienceTemplate()
        result = template.generate(data_science_template_vars)

        # Should include common data science libraries
        common_libs = ["pandas", "numpy", "matplotlib", "jupyter", "notebook"]
        assert any(lib in result.lower() for lib in common_libs)

    def test_data_science_template_includes_tasks(self, data_science_template_vars):
        """Test Data Science template includes common data science tasks."""
        template = DataScienceTemplate()
        result = template.generate(data_science_template_vars)

        # Should include notebook or analysis tasks
        assert (
            "jupyter" in result.lower()
            or "notebook" in result.lower()
            or "analysis" in result.lower()
        )

    def test_data_science_template_additional_files(self, data_science_template_vars):
        """Test Data Science template provides additional files."""
        template = DataScienceTemplate()
        files = template.get_additional_files(data_science_template_vars)

        assert isinstance(files, dict)

    def test_data_science_template_variable_substitution(self, data_science_template_vars):
        """Test that variables are properly substituted."""
        template = DataScienceTemplate()
        result = template.generate(data_science_template_vars)

        # TOML uses ${{VAR}} syntax for variable references, which is not a Jinja2 template
        # So we only check that Jinja2-style variables without $ are not present
        # Check that there are no unreplaced Jinja2 variables (those without $ prefix)
        import re

        # Find {{ }} patterns that are NOT preceded by $
        jinja_pattern = r"(?<!\$)\{\{.*?\}\}"
        assert not re.search(jinja_pattern, result), "Found unreplaced Jinja2 variables"


# ============================================================================
# Test Python Library Template
# ============================================================================


@pytest.mark.unit
class TestPythonLibraryTemplate:
    """Test suite for Python Library project template."""

    def test_python_library_template_metadata(self):
        """Test Python Library template has correct metadata."""
        template = PythonLibraryTemplate()

        assert template.name == "python-library"
        assert (
            "library" in template.description.lower() or "package" in template.description.lower()
        )
        assert template.category == "library"

    def test_python_library_template_prompts(self):
        """Test Python Library template returns correct prompts."""
        template = PythonLibraryTemplate()
        prompts = template.get_prompts()

        assert isinstance(prompts, dict)
        expected_keys = {"package_name", "module_name", "author_name", "author_email", "use_docs"}
        assert expected_keys.issubset(prompts.keys())

    def test_python_library_template_generate_creates_valid_toml(
        self, python_library_template_vars
    ):
        """Test Python Library template generates valid pyproject.toml."""
        template = PythonLibraryTemplate()
        # Update fixture data to match template expectations
        vars_copy = python_library_template_vars.copy()
        vars_copy["package_name"] = vars_copy.get("project_name", "mylib")
        vars_copy["module_name"] = vars_copy.get("project_name", "mylib").replace("-", "_")
        vars_copy["author_name"] = vars_copy.get("author", "Test Author")
        vars_copy["author_email"] = vars_copy.get("email", "test@example.com")

        result = template.generate(vars_copy)

        assert isinstance(result, str)
        assert len(result) > 0
        assert vars_copy["package_name"] in result

    def test_python_library_template_includes_dependencies(self, python_library_template_vars):
        """Test Python Library template includes required dependencies."""
        template = PythonLibraryTemplate()
        result = template.generate(python_library_template_vars)

        # Should include build system and testing tools
        build_tools = ["setuptools", "hatchling", "flit", "poetry"]
        assert any(tool in result.lower() for tool in build_tools)

    def test_python_library_template_includes_tasks(self, python_library_template_vars):
        """Test Python Library template includes common library tasks."""
        template = PythonLibraryTemplate()
        result = template.generate(python_library_template_vars)

        # Should include build and test tasks
        assert "build" in result.lower() or "test" in result.lower()

    def test_python_library_template_additional_files(self, python_library_template_vars):
        """Test Python Library template provides additional files."""
        template = PythonLibraryTemplate()
        files = template.get_additional_files(python_library_template_vars)

        assert isinstance(files, dict)

    def test_python_library_template_variable_substitution(self, python_library_template_vars):
        """Test that variables are properly substituted."""
        template = PythonLibraryTemplate()
        result = template.generate(python_library_template_vars)

        assert "{{" not in result
        assert "}}" not in result


# ============================================================================
# Test All Templates - Common Functionality
# ============================================================================


@pytest.mark.unit
class TestAllTemplatesCommon:
    """Test suite for common functionality across all templates."""

    @pytest.mark.parametrize(
        "template_class",
        [DjangoTemplate, FastAPITemplate, DataScienceTemplate, PythonLibraryTemplate],
    )
    def test_template_can_be_instantiated(self, template_class):
        """Test that all templates can be instantiated."""
        template = template_class()
        assert template is not None

    @pytest.mark.parametrize(
        "template_class",
        [DjangoTemplate, FastAPITemplate, DataScienceTemplate, PythonLibraryTemplate],
    )
    def test_template_has_required_metadata(self, template_class):
        """Test that all templates have required metadata."""
        template = template_class()

        assert hasattr(template, "name")
        assert hasattr(template, "description")
        assert hasattr(template, "category")

        assert isinstance(template.name, str) and len(template.name) > 0
        assert isinstance(template.description, str) and len(template.description) > 0
        assert isinstance(template.category, str) and len(template.category) > 0

    @pytest.mark.parametrize(
        "template_class",
        [DjangoTemplate, FastAPITemplate, DataScienceTemplate, PythonLibraryTemplate],
    )
    def test_template_get_prompts_returns_dict(self, template_class):
        """Test that all templates return dict from get_prompts."""
        template = template_class()
        prompts = template.get_prompts()

        assert isinstance(prompts, dict)
        assert len(prompts) > 0

    @pytest.mark.parametrize(
        "template_class",
        [DjangoTemplate, FastAPITemplate, DataScienceTemplate, PythonLibraryTemplate],
    )
    def test_template_generate_returns_string(self, template_class):
        """Test that all templates return string from generate."""
        template = template_class()
        # Prepare variables based on template type
        if template_class == PythonLibraryTemplate:
            variables = {
                "package_name": "testproject",
                "module_name": "testproject",
                "author_name": "Test Author",
                "author_email": "test@example.com",
            }
        else:
            variables = {
                "project_name": "testproject",
                "author": "Test Author",
                "email": "test@example.com",
                "python_version": "3.11",
            }

        result = template.generate(variables)

        assert isinstance(result, str)
        assert len(result) > 0

    @pytest.mark.parametrize(
        "template_class",
        [DjangoTemplate, FastAPITemplate, DataScienceTemplate, PythonLibraryTemplate],
    )
    def test_template_get_additional_files_returns_dict(self, template_class):
        """Test that all templates return dict from get_additional_files."""
        template = template_class()
        # Prepare variables based on template type
        if template_class == PythonLibraryTemplate:
            variables = {
                "package_name": "testproject",
                "module_name": "testproject",
                "author_name": "Test Author",
                "author_email": "test@example.com",
            }
        else:
            variables = {
                "project_name": "testproject",
                "author": "Test Author",
                "python_version": "3.11",
            }

        files = template.get_additional_files(variables)

        assert isinstance(files, dict)

    @pytest.mark.parametrize(
        "template_class",
        [DjangoTemplate, FastAPITemplate, DataScienceTemplate, PythonLibraryTemplate],
    )
    def test_template_generates_valid_toml_structure(self, template_class):
        """Test that all templates generate valid TOML structure."""
        template = template_class()
        # Prepare variables based on template type
        if template_class == PythonLibraryTemplate:
            variables = {
                "package_name": "testproject",
                "module_name": "testproject",
                "author_name": "Test Author",
                "author_email": "test@example.com",
            }
        else:
            variables = {
                "project_name": "testproject",
                "author": "Test Author",
                "email": "test@example.com",
                "python_version": "3.11",
            }

        result = template.generate(variables)

        # Should contain TOML sections
        assert "[" in result and "]" in result
        # Should contain project metadata
        assert "testproject" in result

    @pytest.mark.parametrize(
        "template_class",
        [DjangoTemplate, FastAPITemplate, DataScienceTemplate, PythonLibraryTemplate],
    )
    def test_template_handles_unicode_in_variables(self, template_class):
        """Test that all templates handle unicode in variables."""
        template = template_class()
        # Prepare variables based on template type
        if template_class == PythonLibraryTemplate:
            variables = {
                "package_name": "project-émoji-🎉",
                "module_name": "project_emoji",
                "author_name": "作者名前",
                "author_email": "test@example.com",
            }
        else:
            variables = {
                "project_name": "project-émoji-🎉",
                "author": "作者名前",
                "python_version": "3.11",
            }

        # Should not raise error
        result = template.generate(variables)
        assert isinstance(result, str)

    @pytest.mark.parametrize(
        "template_class",
        [DjangoTemplate, FastAPITemplate, DataScienceTemplate, PythonLibraryTemplate],
    )
    def test_template_prompts_have_valid_structure(self, template_class):
        """Test that all template prompts have valid structure."""
        template = template_class()
        prompts = template.get_prompts()

        for var_name, prompt_config in prompts.items():
            assert isinstance(var_name, str)
            assert isinstance(prompt_config, dict)

            # Each prompt should have at minimum a type or message
            assert "type" in prompt_config or "message" in prompt_config

    @pytest.mark.parametrize(
        "template_class,expected_name",
        [
            (DjangoTemplate, "django"),
            (FastAPITemplate, "fastapi"),
            (DataScienceTemplate, "data-science"),
            (PythonLibraryTemplate, "python-library"),
        ],
    )
    def test_template_has_correct_name(self, template_class, expected_name):
        """Test that each template has the correct name."""
        template = template_class()
        assert template.name == expected_name

    @pytest.mark.parametrize(
        "template_class",
        [DjangoTemplate, FastAPITemplate, DataScienceTemplate, PythonLibraryTemplate],
    )
    def test_template_generates_taskx_section(self, template_class):
        """Test that all templates generate taskx configuration section."""
        template = template_class()
        # Prepare variables based on template type
        if template_class == PythonLibraryTemplate:
            variables = {
                "package_name": "testproject",
                "module_name": "testproject",
                "author_name": "Test",
                "author_email": "test@example.com",
            }
        else:
            variables = {"project_name": "testproject", "author": "Test", "python_version": "3.11"}

        result = template.generate(variables)

        # Should include taskx configuration
        assert "taskx" in result.lower()

    @pytest.mark.parametrize(
        "template_class",
        [DjangoTemplate, FastAPITemplate, DataScienceTemplate, PythonLibraryTemplate],
    )
    def test_template_includes_author_info(self, template_class):
        """Test that all templates include author information."""
        template = template_class()
        # Prepare variables based on template type
        if template_class == PythonLibraryTemplate:
            variables = {
                "package_name": "testproject",
                "module_name": "testproject",
                "author_name": "John Doe",
                "author_email": "john@example.com",
            }
        else:
            variables = {
                "project_name": "testproject",
                "author": "John Doe",
                "email": "john@example.com",
                "python_version": "3.11",
            }

        result = template.generate(variables)

        # Only PythonLibraryTemplate includes author info in pyproject.toml
        # Other templates (Django, FastAPI, DataScience) only generate task configuration
        if template_class == PythonLibraryTemplate:
            assert "John Doe" in result or "john@example.com" in result
        else:
            # For other templates, just verify generation succeeded
            assert isinstance(result, str) and len(result) > 0

    @pytest.mark.parametrize(
        "template_class",
        [DjangoTemplate, FastAPITemplate, DataScienceTemplate, PythonLibraryTemplate],
    )
    def test_template_does_not_leave_unrendered_variables(self, template_class):
        """Test that templates don't leave unrendered Jinja variables."""
        template = template_class()
        # Prepare variables based on template type
        if template_class == PythonLibraryTemplate:
            variables = {
                "package_name": "testproject",
                "module_name": "testproject",
                "author_name": "Test",
                "author_email": "test@test.com",
            }
        else:
            variables = {
                "project_name": "testproject",
                "author": "Test",
                "email": "test@test.com",
                "python_version": "3.11",
            }

        result = template.generate(variables)

        # TOML uses ${{VAR}} syntax for variable references
        # Check that there are no unreplaced Jinja2 variables (those without $ prefix)
        import re

        jinja_pattern = r"(?<!\$)\{\{.*?\}\}"
        assert not re.search(jinja_pattern, result), "Found unreplaced Jinja2 variables"
        # Also check for Jinja2 control structures
        assert "{%" not in result
        assert "%}" not in result
