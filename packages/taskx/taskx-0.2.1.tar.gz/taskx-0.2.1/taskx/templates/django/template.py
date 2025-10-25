"""
Django web application template.

Copyright (c) 2025 taskx Project
Licensed under Proprietary License - See LICENSE file
"""

from typing import Any, Dict

from taskx.templates.base import Template


class DjangoTemplate(Template):
    """Django web application with database migrations and testing."""

    name = "django"
    description = "Django web application with database migrations, testing, and deployment"
    category = "web"

    def get_prompts(self) -> Dict[str, Any]:
        """Get prompts for Django template variables."""
        return {
            "project_name": {
                "type": "text",
                "message": "Project name:",
                "default": "myproject",
            },
            "use_celery": {
                "type": "confirm",
                "message": "Include Celery for background tasks?",
                "default": False,
            },
            "use_docker": {
                "type": "confirm",
                "message": "Include Docker configuration?",
                "default": True,
            },
        }

    def generate(self, variables: Dict[str, str]) -> str:
        """Generate Django pyproject.toml."""
        project_name = variables.get("project_name", "myproject")
        use_celery = variables.get("use_celery", "False") == "True"
        use_docker = variables.get("use_docker", "True") == "True"

        # Build task list
        tasks = f"""[project]
name = "{project_name}"
version = "0.1.0"
description = "Django web application"
requires-python = ">=3.8"

[tool.taskx.env]
DJANGO_SETTINGS_MODULE = "{project_name}.settings"
PYTHON = "python3"

[tool.taskx.tasks]
# Development
dev = {{ cmd = "${{PYTHON}} manage.py runserver", watch = ["**/*.py", "templates/**/*"], description = "Start development server" }}
shell = {{ cmd = "${{PYTHON}} manage.py shell", description = "Start Django shell" }}

# Database
migrate = {{ cmd = "${{PYTHON}} manage.py migrate", description = "Run database migrations" }}
makemigrations = {{ cmd = "${{PYTHON}} manage.py makemigrations", description = "Create database migrations" }}
db-reset = {{ cmd = "${{PYTHON}} manage.py flush --no-input", confirm = "Delete all data from database?", description = "Reset database" }}

# Testing
test = {{ cmd = "pytest", description = "Run tests" }}
test-cov = {{ cmd = "pytest --cov={project_name} --cov-report=html", description = "Run tests with coverage" }}

# Code quality
lint = {{ parallel = ["ruff check .", "mypy ."], description = "Run linting" }}
format = {{ cmd = "black . && isort .", description = "Format code" }}
check = {{ parallel = ["ruff check .", "mypy .", "pytest -q"], description = "Run all checks" }}

# Static files
collectstatic = {{ cmd = "${{PYTHON}} manage.py collectstatic --no-input", description = "Collect static files" }}
"""

        # Add Celery tasks if enabled
        if use_celery:
            tasks += """
# Celery
celery-worker = { cmd = "celery -A ${PROJECT_NAME} worker -l info", description = "Start Celery worker" }
celery-beat = { cmd = "celery -A ${PROJECT_NAME} beat -l info", description = "Start Celery beat scheduler" }
"""

        # Add Docker tasks if enabled
        if use_docker:
            tasks += """
# Docker
docker-build = { cmd = "docker-compose build", description = "Build Docker images" }
docker-up = { cmd = "docker-compose up -d", description = "Start Docker containers" }
docker-down = { cmd = "docker-compose down", description = "Stop Docker containers" }
docker-logs = { cmd = "docker-compose logs -f", description = "View Docker logs" }
"""

        # Add deployment task
        tasks += """
# Deployment
deploy = { depends = ["check", "collectstatic"], cmd = "sh deploy.sh", confirm = "Deploy to production?", description = "Deploy to production" }
"""

        return tasks

    def get_additional_files(self, variables: Dict[str, str]) -> Dict[str, str]:
        """Generate additional files for Django project."""
        files = {}

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

# Django
*.log
local_settings.py
db.sqlite3
media/
staticfiles/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db
"""

        # README.md
        project_name = variables.get("project_name", "myproject")
        files[
            "README.md"
        ] = f"""# {project_name}

Django web application built with taskx.

## Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Run migrations
taskx migrate

# Start development server
taskx dev
```

## Available Tasks

```bash
taskx list           # See all available tasks
taskx dev            # Start development server
taskx test           # Run tests
taskx check          # Run all quality checks
```

## Development

- Run `taskx dev` to start the development server with auto-reload
- Run `taskx makemigrations` after model changes
- Run `taskx test` before committing

## Deployment

```bash
taskx deploy         # Deploy to production (with confirmation)
```
"""

        return files
