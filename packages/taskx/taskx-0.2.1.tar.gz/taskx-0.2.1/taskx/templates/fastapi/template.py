"""
FastAPI microservice template.

Copyright (c) 2025 taskx Project
Licensed under Proprietary License - See LICENSE file
"""

from typing import Any, Dict

from taskx.templates.base import Template


class FastAPITemplate(Template):
    """FastAPI API microservice with testing and Docker."""

    name = "fastapi"
    description = "FastAPI microservice with async support, testing, and Docker deployment"
    category = "web"

    def get_prompts(self) -> Dict[str, Any]:
        """Get prompts for FastAPI template variables."""
        return {
            "project_name": {
                "type": "text",
                "message": "Project name:",
                "default": "my-api",
            },
            "use_database": {
                "type": "confirm",
                "message": "Include database integration (SQLAlchemy)?",
                "default": True,
            },
            "use_docker": {
                "type": "confirm",
                "message": "Include Docker configuration?",
                "default": True,
            },
        }

    def generate(self, variables: Dict[str, str]) -> str:
        """Generate FastAPI pyproject.toml."""
        project_name = variables.get("project_name", "my-api")
        use_database = variables.get("use_database", "True") == "True"
        use_docker = variables.get("use_docker", "True") == "True"

        tasks = f"""[project]
name = "{project_name}"
version = "0.1.0"
description = "FastAPI microservice"
requires-python = ">=3.8"

[tool.taskx.env]
APP_MODULE = "app.main:app"
HOST = "0.0.0.0"
PORT = "8000"

[tool.taskx.tasks]
# Development
dev = {{ cmd = "uvicorn ${{APP_MODULE}} --host ${{HOST}} --port ${{PORT}} --reload", watch = ["**/*.py"], description = "Start development server with auto-reload" }}
shell = {{ cmd = "python -m IPython", description = "Start Python shell" }}

# Testing
test = {{ cmd = "pytest tests/ -v", description = "Run tests" }}
test-cov = {{ cmd = "pytest tests/ --cov=app --cov-report=html --cov-report=term", description = "Run tests with coverage" }}
test-watch = {{ cmd = "pytest-watch tests/", description = "Run tests in watch mode" }}

# Code quality
lint = {{ parallel = ["ruff check .", "mypy app/"], description = "Run linting" }}
format = {{ cmd = "black . && isort .", description = "Format code" }}
check = {{ parallel = ["ruff check .", "mypy app/", "pytest tests/ -q"], description = "Run all checks" }}
"""

        # Add database tasks if enabled
        if use_database:
            tasks += """
# Database
db-migrate = { cmd = "alembic upgrade head", description = "Run database migrations" }
db-revision = { cmd = "alembic revision --autogenerate -m 'migration'", description = "Create new migration" }
db-rollback = { cmd = "alembic downgrade -1", description = "Rollback last migration" }
db-reset = { cmd = "alembic downgrade base && alembic upgrade head", confirm = "Reset database?", description = "Reset database" }
"""

        # Add Docker tasks if enabled
        if use_docker:
            tasks += """
# Docker
docker-build = { cmd = "docker build -t ${PROJECT_NAME}:latest .", description = "Build Docker image" }
docker-run = { cmd = "docker run -p ${PORT}:${PORT} --env-file .env ${PROJECT_NAME}:latest", description = "Run Docker container" }
docker-compose-up = { cmd = "docker-compose up -d", description = "Start services with docker-compose" }
docker-compose-down = { cmd = "docker-compose down", description = "Stop services" }
docker-compose-logs = { cmd = "docker-compose logs -f app", description = "View application logs" }
"""

        # Add deployment tasks
        tasks += """
# API Documentation
docs = { cmd = "echo 'API docs: http://localhost:${PORT}/docs'", description = "Open API documentation" }
openapi = { cmd = "python -c 'import json; from app.main import app; print(json.dumps(app.openapi(), indent=2))' > openapi.json", description = "Export OpenAPI schema" }

# Deployment
deploy = { depends = ["check"], cmd = "sh deploy.sh", confirm = "Deploy to production?", description = "Deploy to production" }
"""

        return tasks

    def get_additional_files(self, variables: Dict[str, str]) -> Dict[str, str]:
        """Generate additional files for FastAPI project."""
        files = {}
        project_name = variables.get("project_name", "my-api")

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

# FastAPI
.env
.env.*
!.env.example

# Testing
.pytest_cache/
.coverage
htmlcov/

# Database
*.db
*.sqlite3

# IDE
.vscode/
.idea/
*.swp

# OS
.DS_Store
"""

        # README.md
        files[
            "README.md"
        ] = f"""# {project_name}

FastAPI microservice built with taskx.

## Features

- ⚡ FastAPI with async support
- 🔍 Automatic API documentation
- 🧪 Testing with pytest
- 🐳 Docker support
- 🔄 Auto-reload in development

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Start development server
taskx dev

# Visit http://localhost:8000/docs for API documentation
```

## Available Tasks

```bash
taskx list           # See all available tasks
taskx dev            # Start development server
taskx test           # Run tests
taskx check          # Run all quality checks
taskx docs           # Open API docs
```

## API Documentation

The API documentation is automatically generated and available at:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **OpenAPI JSON:** http://localhost:8000/openapi.json

## Testing

```bash
taskx test           # Run all tests
taskx test-cov       # Run tests with coverage report
taskx test-watch     # Run tests in watch mode
```

## Docker

```bash
taskx docker-build   # Build Docker image
taskx docker-run     # Run container
```

## Deployment

```bash
taskx deploy         # Deploy to production (requires confirmation)
```
"""

        # .env.example
        files[
            ".env.example"
        ] = f"""# {project_name} Environment Variables

# Application
APP_NAME={project_name}
APP_VERSION=0.1.0
DEBUG=True

# Server
HOST=0.0.0.0
PORT=8000

# Database (if using database)
DATABASE_URL=postgresql://user:password@localhost/dbname

# Security
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
"""

        return files
