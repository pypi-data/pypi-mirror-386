"""
Python Library / Package template.

Copyright (c) 2025 taskx Project
Licensed under Proprietary License - See LICENSE file
"""

from typing import Any, Dict

from taskx.templates.base import Template


class PythonLibraryTemplate(Template):
    """Python library/package with testing, docs, and PyPI publishing."""

    name = "python-library"
    description = "Python library/package with testing, documentation, and PyPI publishing workflow"
    category = "library"

    def get_prompts(self) -> Dict[str, Any]:
        """Get prompts for Python Library template variables."""
        return {
            "package_name": {
                "type": "text",
                "message": "Package name (lowercase, with hyphens):",
                "default": "my-package",
            },
            "module_name": {
                "type": "text",
                "message": "Module name (lowercase, with underscores):",
                "default": "my_package",
            },
            "author_name": {
                "type": "text",
                "message": "Author name:",
                "default": "Your Name",
            },
            "author_email": {
                "type": "text",
                "message": "Author email:",
                "default": "you@example.com",
            },
            "use_docs": {
                "type": "confirm",
                "message": "Include documentation setup (mkdocs)?",
                "default": True,
            },
        }

    def generate(self, variables: Dict[str, str]) -> str:
        """Generate Python Library pyproject.toml."""
        package_name = variables.get("package_name", "my-package")
        module_name = variables.get("module_name", "my_package")
        author_name = variables.get("author_name", "Your Name")
        author_email = variables.get("author_email", "you@example.com")
        use_docs = variables.get("use_docs", "True") == "True"

        tasks = f"""[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "{package_name}"
version = "0.1.0"
description = "A Python library built with taskx"
readme = "README.md"
requires-python = ">=3.8"
license = {{text = "MIT"}}
authors = [
    {{name = "{author_name}", email = "{author_email}"}}
]
keywords = ["python", "library"]
classifiers = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.8",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
]

dependencies = []

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-cov>=4.0.0",
    "mypy>=1.0.0",
    "ruff>=0.1.0",
    "black>=23.0.0",
    "isort>=5.12.0",
]

[project.urls]
Homepage = "https://github.com/yourusername/{package_name}"
Repository = "https://github.com/yourusername/{package_name}"
"Bug Tracker" = "https://github.com/yourusername/{package_name}/issues"

[tool.hatch.build.targets.wheel]
packages = ["{module_name}"]

[tool.taskx.env]
PYTHON = "python3"
PACKAGE_NAME = "{package_name}"
MODULE_NAME = "{module_name}"

[tool.taskx.tasks]
# Development
install = {{ cmd = "pip install -e '.[dev]'", description = "Install package in development mode" }}
install-prod = {{ cmd = "pip install -e .", description = "Install package (production)" }}

# Testing
test = {{ cmd = "pytest tests/ -v", description = "Run tests" }}
test-cov = {{ cmd = "pytest tests/ --cov=${{MODULE_NAME}} --cov-report=html --cov-report=term-missing", description = "Run tests with coverage" }}
test-watch = {{ cmd = "pytest-watch tests/", description = "Run tests in watch mode" }}
test-all = {{ cmd = "pytest tests/ -v --cov=${{MODULE_NAME}}", description = "Run all tests with coverage" }}

# Code quality
format = {{ cmd = "black ${{MODULE_NAME}} tests && isort ${{MODULE_NAME}} tests", description = "Format code with black and isort" }}
lint = {{ cmd = "ruff check ${{MODULE_NAME}} tests", description = "Run linting with ruff" }}
typecheck = {{ cmd = "mypy ${{MODULE_NAME}}", description = "Type check with mypy" }}
check = {{ parallel = ["ruff check ${{MODULE_NAME}} tests", "mypy ${{MODULE_NAME}}", "pytest tests/ -q"], description = "Run all quality checks" }}

# Build
clean = {{ cmd = "rm -rf build dist *.egg-info htmlcov .coverage .pytest_cache .mypy_cache .ruff_cache", description = "Clean build artifacts" }}
build = {{ depends = ["clean"], cmd = "${{PYTHON}} -m build", description = "Build distribution packages" }}
verify = {{ cmd = "twine check dist/*", description = "Verify distribution packages" }}
"""

        # Add documentation tasks if enabled
        if use_docs:
            tasks += """
# Documentation
docs-serve = { cmd = "mkdocs serve", description = "Serve documentation locally" }
docs-build = { cmd = "mkdocs build", description = "Build documentation" }
docs-deploy = { cmd = "mkdocs gh-deploy --force", description = "Deploy docs to GitHub Pages" }
"""

        # Add publishing tasks
        tasks += """
# Publishing
publish-test = { depends = ["check", "build", "verify"], cmd = "twine upload --repository testpypi dist/*", confirm = "Publish to TestPyPI?", description = "Publish to TestPyPI" }
publish = { depends = ["check", "build", "verify"], cmd = "twine upload dist/*", confirm = "Publish to PyPI?", description = "Publish to PyPI" }

# Version management
version-patch = { cmd = "echo 'Bump patch version'", description = "Bump patch version (0.1.0 -> 0.1.1)" }
version-minor = { cmd = "echo 'Bump minor version'", description = "Bump minor version (0.1.0 -> 0.2.0)" }
version-major = { cmd = "echo 'Bump major version'", description = "Bump major version (0.1.0 -> 1.0.0)" }

# Git workflow
tag = { cmd = "git tag v0.1.0 && git push origin v0.1.0", description = "Create and push version tag" }
"""

        return tasks

    def get_additional_files(self, variables: Dict[str, str]) -> Dict[str, str]:
        """Generate additional files for Python Library project."""
        files = {}
        package_name = variables.get("package_name", "my-package")
        module_name = variables.get("module_name", "my_package")
        author_name = variables.get("author_name", "Your Name")

        # .gitignore
        files[
            ".gitignore"
        ] = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
*.egg-info/
dist/
build/

# Testing
.pytest_cache/
.coverage
htmlcov/
.tox/

# Type checking
.mypy_cache/
.dmypy.json
dmypy.json

# Linting
.ruff_cache/

# Documentation
site/
docs/_build/

# IDE
.vscode/
.idea/
*.swp

# OS
.DS_Store
Thumbs.db
"""

        # README.md
        files[
            "README.md"
        ] = f"""# {package_name}

A Python library built with taskx.

## Installation

```bash
pip install {package_name}
```

## Usage

```python
import {module_name}

# Your code here
```

## Development

### Setup

```bash
# Clone repository
git clone https://github.com/yourusername/{package_name}.git
cd {package_name}

# Install in development mode
taskx install
```

### Testing

```bash
taskx test           # Run tests
taskx test-cov       # Run tests with coverage
taskx test-watch     # Run tests in watch mode
```

### Code Quality

```bash
taskx format         # Format code
taskx lint           # Run linting
taskx typecheck      # Type checking
taskx check          # Run all checks
```

### Building & Publishing

```bash
# Build package
taskx build

# Verify package
taskx verify

# Publish to TestPyPI
taskx publish-test

# Publish to PyPI
taskx publish
```

## Documentation

Full documentation is available at [https://yourusername.github.io/{package_name}](https://yourusername.github.io/{package_name})

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Author

{author_name}
"""

        # LICENSE
        files[
            "LICENSE"
        ] = f"""MIT License

Copyright (c) 2025 {author_name}

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

        # Package __init__.py
        files[
            f"{module_name}/__init__.py"
        ] = f'''"""
{package_name}

A Python library built with taskx.
"""

__version__ = "0.1.0"
__author__ = "{author_name}"

# Your package exports here
'''

        # Basic test file
        files[
            "tests/test_basic.py"
        ] = f'''"""
Basic tests for {module_name}.
"""

import {module_name}


def test_version():
    """Test version is defined."""
    assert hasattr({module_name}, "__version__")
    assert isinstance({module_name}.__version__, str)


def test_import():
    """Test package can be imported."""
    assert {module_name} is not None
'''

        return files
