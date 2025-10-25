"""
Task templates for project initialization.

Copyright (c) 2025 taskx Project
Licensed under Proprietary License - See LICENSE file
"""

from typing import Dict, List, Optional

from taskx.templates.base import Template
from taskx.templates.data_science.template import DataScienceTemplate
from taskx.templates.django.template import DjangoTemplate
from taskx.templates.fastapi.template import FastAPITemplate
from taskx.templates.python_library.template import PythonLibraryTemplate

# Template registry
_TEMPLATES: Dict[str, Template] = {
    "django": DjangoTemplate(),
    "fastapi": FastAPITemplate(),
    "data-science": DataScienceTemplate(),
    "python-library": PythonLibraryTemplate(),
}


def get_template(name: str) -> Optional[Template]:
    """Get template by name.

    Args:
        name: Template name (e.g., "django", "fastapi")

    Returns:
        Template instance or None if not found
    """
    return _TEMPLATES.get(name)


def list_templates() -> List[Dict[str, str]]:
    """List all available templates.

    Returns:
        List of dicts with template info (name, description, category)
    """
    return [
        {
            "name": template.name,
            "description": template.description,
            "category": template.category,
        }
        for template in _TEMPLATES.values()
    ]


def get_templates_by_category() -> Dict[str, List[Template]]:
    """Group templates by category.

    Returns:
        Dict mapping category name to list of templates
    """
    result: Dict[str, List[Template]] = {}
    for template in _TEMPLATES.values():
        category = template.category
        if category not in result:
            result[category] = []
        result[category].append(template)
    return result


__all__ = [
    "Template",
    "get_template",
    "list_templates",
    "get_templates_by_category",
    "DjangoTemplate",
    "FastAPITemplate",
    "DataScienceTemplate",
    "PythonLibraryTemplate",
]
