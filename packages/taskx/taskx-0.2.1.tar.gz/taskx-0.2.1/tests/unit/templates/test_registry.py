"""
Unit tests for template registry.

Tests template registration, retrieval, and listing functionality.
"""

import pytest

from taskx.templates import (
    DataScienceTemplate,
    DjangoTemplate,
    FastAPITemplate,
    PythonLibraryTemplate,
    get_template,
    get_templates_by_category,
    list_templates,
)

# ============================================================================
# Test get_template
# ============================================================================


@pytest.mark.unit
class TestGetTemplate:
    """Test suite for get_template function."""

    def test_get_template_django(self):
        """Test retrieving Django template."""
        template = get_template("django")

        assert template is not None
        assert isinstance(template, DjangoTemplate)
        assert template.name == "django"

    def test_get_template_fastapi(self):
        """Test retrieving FastAPI template."""
        template = get_template("fastapi")

        assert template is not None
        assert isinstance(template, FastAPITemplate)
        assert template.name == "fastapi"

    def test_get_template_data_science(self):
        """Test retrieving Data Science template."""
        template = get_template("data-science")

        assert template is not None
        assert isinstance(template, DataScienceTemplate)
        assert template.name == "data-science"

    def test_get_template_python_library(self):
        """Test retrieving Python Library template."""
        template = get_template("python-library")

        assert template is not None
        assert isinstance(template, PythonLibraryTemplate)
        assert template.name == "python-library"

    def test_get_template_nonexistent_returns_none(self):
        """Test that requesting non-existent template returns None."""
        template = get_template("nonexistent")

        assert template is None

    def test_get_template_case_sensitive(self):
        """Test that template names are case-sensitive."""
        # "Django" should not match "django"
        template = get_template("Django")

        assert template is None

    def test_get_template_empty_string_returns_none(self):
        """Test that empty string returns None."""
        template = get_template("")

        assert template is None

    @pytest.mark.parametrize("name", ["django", "fastapi", "data-science", "python-library"])
    def test_get_template_all_registered_templates(self, name):
        """Test that all registered templates can be retrieved."""
        template = get_template(name)

        assert template is not None
        assert template.name == name

    def test_get_template_returns_same_instance(self):
        """Test that get_template returns same instance on multiple calls."""
        template1 = get_template("django")
        template2 = get_template("django")

        # Should return same instance (singleton behavior)
        assert template1 is template2

    def test_get_template_with_whitespace(self):
        """Test that whitespace in name doesn't match."""
        template = get_template(" django ")

        assert template is None


# ============================================================================
# Test list_templates
# ============================================================================


@pytest.mark.unit
class TestListTemplates:
    """Test suite for list_templates function."""

    def test_list_templates_returns_list(self):
        """Test that list_templates returns a list."""
        templates = list_templates()

        assert isinstance(templates, list)
        assert len(templates) > 0

    def test_list_templates_returns_dicts(self):
        """Test that list_templates returns list of dicts."""
        templates = list_templates()

        assert all(isinstance(t, dict) for t in templates)

    def test_list_templates_includes_all_templates(self):
        """Test that list_templates includes all registered templates."""
        templates = list_templates()

        names = [t["name"] for t in templates]
        expected_names = ["django", "fastapi", "data-science", "python-library"]

        for expected in expected_names:
            assert expected in names

    def test_list_templates_includes_required_fields(self):
        """Test that each template entry has required fields."""
        templates = list_templates()

        for template in templates:
            assert "name" in template
            assert "description" in template
            assert "category" in template

            assert isinstance(template["name"], str)
            assert isinstance(template["description"], str)
            assert isinstance(template["category"], str)

            assert len(template["name"]) > 0
            assert len(template["description"]) > 0
            assert len(template["category"]) > 0

    def test_list_templates_count(self):
        """Test that list_templates returns expected number of templates."""
        templates = list_templates()

        # Should have exactly 4 templates
        assert len(templates) == 4

    def test_list_templates_no_duplicates(self):
        """Test that list_templates has no duplicate entries."""
        templates = list_templates()
        names = [t["name"] for t in templates]

        assert len(names) == len(set(names))

    def test_list_templates_descriptions_are_descriptive(self):
        """Test that template descriptions are meaningful."""
        templates = list_templates()

        for template in templates:
            # Description should be more than just the name
            assert len(template["description"]) > len(template["name"])
            # Should have actual content
            assert len(template["description"]) > 10


# ============================================================================
# Test get_templates_by_category
# ============================================================================


@pytest.mark.unit
class TestGetTemplatesByCategory:
    """Test suite for get_templates_by_category function."""

    def test_get_templates_by_category_returns_dict(self):
        """Test that function returns a dictionary."""
        templates = get_templates_by_category()

        assert isinstance(templates, dict)
        assert len(templates) > 0

    def test_get_templates_by_category_has_web_category(self):
        """Test that web category exists."""
        templates = get_templates_by_category()

        assert "web" in templates
        assert isinstance(templates["web"], list)
        assert len(templates["web"]) > 0

    def test_get_templates_by_category_has_data_category(self):
        """Test that data category exists."""
        templates = get_templates_by_category()

        assert "data" in templates
        assert isinstance(templates["data"], list)

    def test_get_templates_by_category_has_library_category(self):
        """Test that library category exists."""
        templates = get_templates_by_category()

        assert "library" in templates
        assert isinstance(templates["library"], list)

    def test_get_templates_by_category_django_in_web(self):
        """Test that Django template is in web category."""
        templates = get_templates_by_category()

        web_templates = templates.get("web", [])
        django_templates = [t for t in web_templates if t.name == "django"]

        assert len(django_templates) == 1

    def test_get_templates_by_category_fastapi_in_web(self):
        """Test that FastAPI template is in web category."""
        templates = get_templates_by_category()

        web_templates = templates.get("web", [])
        fastapi_templates = [t for t in web_templates if t.name == "fastapi"]

        assert len(fastapi_templates) == 1

    def test_get_templates_by_category_data_science_in_data(self):
        """Test that Data Science template is in data category."""
        templates = get_templates_by_category()

        data_templates = templates.get("data", [])
        ds_templates = [t for t in data_templates if t.name == "data-science"]

        assert len(ds_templates) == 1

    def test_get_templates_by_category_python_library_in_library(self):
        """Test that Python Library template is in library category."""
        templates = get_templates_by_category()

        library_templates = templates.get("library", [])
        lib_templates = [t for t in library_templates if t.name == "python-library"]

        assert len(lib_templates) == 1

    def test_get_templates_by_category_all_templates_categorized(self):
        """Test that all templates are in some category."""
        templates = get_templates_by_category()

        all_templates = []
        for category_templates in templates.values():
            all_templates.extend(category_templates)

        # Should have all 4 templates
        assert len(all_templates) == 4

    def test_get_templates_by_category_no_duplicates(self):
        """Test that templates don't appear in multiple categories."""
        templates = get_templates_by_category()

        seen_names = set()
        for category_templates in templates.values():
            for template in category_templates:
                assert template.name not in seen_names
                seen_names.add(template.name)


# ============================================================================
# Test Template Registry Integrity
# ============================================================================


@pytest.mark.unit
class TestTemplateRegistryIntegrity:
    """Test suite for template registry integrity."""

    def test_all_templates_have_unique_names(self):
        """Test that all templates have unique names."""
        templates = list_templates()
        names = [t["name"] for t in templates]

        assert len(names) == len(set(names))

    def test_all_templates_can_be_retrieved(self):
        """Test that all listed templates can be retrieved."""
        templates = list_templates()

        for template_info in templates:
            name = template_info["name"]
            template = get_template(name)

            assert template is not None
            assert template.name == name

    def test_registry_consistency(self):
        """Test that registry is consistent across calls."""
        templates1 = list_templates()
        templates2 = list_templates()

        # Should return same data
        assert len(templates1) == len(templates2)

        names1 = sorted([t["name"] for t in templates1])
        names2 = sorted([t["name"] for t in templates2])

        assert names1 == names2

    def test_all_templates_have_valid_metadata(self):
        """Test that all templates have valid metadata."""
        templates = list_templates()

        for template_info in templates:
            name = template_info["name"]
            template = get_template(name)

            assert template is not None
            assert template.name == template_info["name"]
            assert template.description == template_info["description"]
            assert template.category == template_info["category"]

    def test_template_categories_are_consistent(self):
        """Test that template categories are consistent."""
        templates = list_templates()
        templates_by_cat = get_templates_by_category()

        # Count templates by category from list_templates
        category_counts = {}
        for template in templates:
            cat = template["category"]
            category_counts[cat] = category_counts.get(cat, 0) + 1

        # Count templates by category from get_templates_by_category
        cat_counts_2 = {cat: len(temps) for cat, temps in templates_by_cat.items()}

        assert category_counts == cat_counts_2

    def test_all_registered_templates_are_functional(self):
        """Test that all registered templates are functional."""
        templates = list_templates()

        for template_info in templates:
            name = template_info["name"]
            template = get_template(name)

            assert template is not None

            # Should be able to get prompts
            prompts = template.get_prompts()
            assert isinstance(prompts, dict)

            # Should be able to generate with basic variables
            variables = {"project_name": "test", "author": "Test", "python_version": "3.11"}
            result = template.generate(variables)
            assert isinstance(result, str)
            assert len(result) > 0

    def test_template_names_follow_convention(self):
        """Test that template names follow naming convention."""
        templates = list_templates()

        for template in templates:
            name = template["name"]
            # Should be lowercase and use hyphens
            assert name == name.lower()
            assert " " not in name

    @pytest.mark.parametrize(
        "expected_name", ["django", "fastapi", "data-science", "python-library"]
    )
    def test_specific_template_is_registered(self, expected_name):
        """Test that specific templates are registered."""
        templates = list_templates()
        names = [t["name"] for t in templates]

        assert expected_name in names

    def test_template_registry_is_immutable(self):
        """Test that template instances are consistent."""
        # Get template twice
        template1 = get_template("django")
        template2 = get_template("django")

        # Should be same instance
        assert template1 is template2

        # Metadata should match
        assert template1.name == template2.name
        assert template1.description == template2.description

    def test_category_grouping_completeness(self):
        """Test that category grouping includes all templates."""
        all_templates = list_templates()
        templates_by_cat = get_templates_by_category()

        # Count total templates
        total_in_categories = sum(len(temps) for temps in templates_by_cat.values())

        assert total_in_categories == len(all_templates)
