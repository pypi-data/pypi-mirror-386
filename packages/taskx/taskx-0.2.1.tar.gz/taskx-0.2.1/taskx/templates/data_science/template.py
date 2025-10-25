"""
Data Science / Machine Learning project template.

Copyright (c) 2025 taskx Project
Licensed under Proprietary License - See LICENSE file
"""

from typing import Any, Dict

from taskx.templates.base import Template


class DataScienceTemplate(Template):
    """Data Science project with ML pipeline, notebooks, and experiment tracking."""

    name = "data-science"
    description = "Data Science project with ML pipeline, Jupyter notebooks, and MLflow tracking"
    category = "data"

    def get_prompts(self) -> Dict[str, Any]:
        """Get prompts for Data Science template variables."""
        return {
            "project_name": {
                "type": "text",
                "message": "Project name:",
                "default": "ml-project",
            },
            "ml_framework": {
                "type": "select",
                "message": "Machine learning framework:",
                "choices": ["scikit-learn", "pytorch", "tensorflow", "both"],
                "default": "scikit-learn",
            },
            "use_mlflow": {
                "type": "confirm",
                "message": "Include MLflow for experiment tracking?",
                "default": True,
            },
        }

    def generate(self, variables: Dict[str, str]) -> str:
        """Generate Data Science pyproject.toml."""
        project_name = variables.get("project_name", "ml-project")
        ml_framework = variables.get("ml_framework", "scikit-learn")
        use_mlflow = variables.get("use_mlflow", "True") == "True"

        tasks = f"""[project]
name = "{project_name}"
version = "0.1.0"
description = "Data Science / Machine Learning project"
requires-python = ">=3.8"

[tool.taskx.env]
PYTHON = "python3"
DATA_DIR = "data"
MODELS_DIR = "models"
NOTEBOOKS_DIR = "notebooks"

[tool.taskx.tasks]
# Jupyter
notebook = {{ cmd = "jupyter lab --notebook-dir=${{NOTEBOOKS_DIR}}", description = "Start Jupyter Lab" }}
notebook-export = {{ cmd = "jupyter nbconvert --to script ${{NOTEBOOKS_DIR}}/*.ipynb --output-dir=scripts", description = "Export notebooks to Python scripts" }}

# Data pipeline
data-download = {{ cmd = "${{PYTHON}} scripts/download_data.py", description = "Download dataset" }}
data-clean = {{ depends = ["data-download"], cmd = "${{PYTHON}} scripts/clean_data.py", description = "Clean and preprocess data" }}
data-split = {{ depends = ["data-clean"], cmd = "${{PYTHON}} scripts/split_data.py", description = "Split into train/val/test sets" }}
data-validate = {{ cmd = "${{PYTHON}} scripts/validate_data.py", description = "Validate data quality" }}

# Data pipeline (complete)
pipeline = {{ depends = ["data-download", "data-clean", "data-split", "data-validate"], cmd = "echo 'Data pipeline complete!'", description = "Run complete data pipeline" }}

# Model training
train = {{ depends = ["pipeline"], cmd = "${{PYTHON}} scripts/train.py", description = "Train model" }}
evaluate = {{ depends = ["train"], cmd = "${{PYTHON}} scripts/evaluate.py", description = "Evaluate model" }}
predict = {{ cmd = "${{PYTHON}} scripts/predict.py", description = "Make predictions" }}

# Hyperparameter tuning
tune = {{ cmd = "${{PYTHON}} scripts/tune_hyperparameters.py", description = "Tune hyperparameters" }}
tune-parallel = {{ parallel = ["${{PYTHON}} scripts/tune.py --config config1.yaml", "${{PYTHON}} scripts/tune.py --config config2.yaml", "${{PYTHON}} scripts/tune.py --config config3.yaml"], description = "Run parallel hyperparameter tuning" }}

# Testing & Quality
test = {{ cmd = "pytest tests/", description = "Run tests" }}
lint = {{ parallel = ["ruff check .", "mypy scripts/"], description = "Run linting" }}
check = {{ parallel = ["pytest tests/ -q", "ruff check ."], description = "Run all checks" }}
"""

        # Add MLflow tasks if enabled
        if use_mlflow:
            tasks += """
# MLflow experiment tracking
mlflow-ui = { cmd = "mlflow ui --port 5000", description = "Start MLflow UI" }
mlflow-list = { cmd = "mlflow experiments list", description = "List experiments" }
mlflow-compare = { cmd = "mlflow runs compare", description = "Compare experiment runs" }
"""

        # Framework-specific tasks
        if ml_framework == "pytorch":
            tasks += """
# PyTorch specific
train-gpu = { cmd = "${{PYTHON}} scripts/train.py --device cuda", description = "Train model on GPU" }
tensorboard = { cmd = "tensorboard --logdir=runs", description = "Start TensorBoard" }
"""
        elif ml_framework == "tensorflow":
            tasks += """
# TensorFlow specific
train-gpu = { cmd = "${{PYTHON}} scripts/train.py --gpu", description = "Train model on GPU" }
tensorboard = { cmd = "tensorboard --logdir=logs", description = "Start TensorBoard" }
"""

        # Additional tasks
        tasks += """
# Model management
model-export = { cmd = "${{PYTHON}} scripts/export_model.py", description = "Export model for production" }
model-serve = { cmd = "${{PYTHON}} scripts/serve_model.py", description = "Serve model via API" }

# Visualization
visualize = { cmd = "${{PYTHON}} scripts/visualize_results.py", description = "Generate visualizations" }}
report = { cmd = "${{PYTHON}} scripts/generate_report.py", description = "Generate analysis report" }

# Deployment
deploy-model = { depends = ["check", "evaluate"], cmd = "sh scripts/deploy.sh", confirm = "Deploy model to production?", description = "Deploy model to production" }
"""

        return tasks

    def get_additional_files(self, variables: Dict[str, str]) -> Dict[str, str]:
        """Generate additional files for Data Science project."""
        files = {}
        project_name = variables.get("project_name", "ml-project")

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

# Data
data/raw/
data/processed/
*.csv
*.parquet
*.h5
*.hdf5

# Models
models/
*.pkl
*.joblib
*.h5
*.pt
*.pth
*.ckpt

# Jupyter
.ipynb_checkpoints/
*.ipynb

# MLflow
mlruns/
mlartifacts/

# TensorBoard
runs/
logs/

# Testing
.pytest_cache/
.coverage
htmlcov/

# IDE
.vscode/
.idea/

# OS
.DS_Store
"""

        # README.md
        ml_framework = variables.get("ml_framework", "scikit-learn")
        files[
            "README.md"
        ] = f"""# {project_name}

Data Science / Machine Learning project built with taskx.

## Features

- 📊 Complete ML pipeline (data → train → evaluate → deploy)
- 📓 Jupyter Lab integration
- 🔬 Experiment tracking with MLflow
- 🚀 Parallel hyperparameter tuning
- 📈 Visualization and reporting
- 🧪 Testing infrastructure

## Framework

- **ML Framework:** {ml_framework}
- **Workflow Management:** taskx

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Start Jupyter Lab
taskx notebook

# Run complete data pipeline
taskx pipeline

# Train model
taskx train

# Evaluate model
taskx evaluate
```

## Data Pipeline

The data pipeline consists of multiple dependent tasks:

```bash
taskx data-download    # Download raw data
taskx data-clean       # Clean and preprocess
taskx data-split       # Split into train/val/test
taskx data-validate    # Validate data quality
taskx pipeline         # Run all data tasks
```

## Model Training

```bash
taskx train            # Train model
taskx evaluate         # Evaluate on test set
taskx tune             # Hyperparameter tuning
taskx tune-parallel    # Parallel tuning (faster)
```

## Experiment Tracking

```bash
taskx mlflow-ui        # Open MLflow UI (http://localhost:5000)
taskx mlflow-list      # List all experiments
taskx mlflow-compare   # Compare runs
```

## Visualization

```bash
taskx visualize        # Generate plots and charts
taskx report           # Generate analysis report
```

## Deployment

```bash
taskx model-export     # Export model for production
taskx model-serve      # Serve model via API
taskx deploy-model     # Deploy to production (with confirmation)
```

## Project Structure

```
{project_name}/
├── data/              # Data files (gitignored)
├── models/            # Trained models (gitignored)
├── notebooks/         # Jupyter notebooks
├── scripts/           # Python scripts
│   ├── download_data.py
│   ├── clean_data.py
│   ├── train.py
│   ├── evaluate.py
│   └── ...
├── tests/             # Unit tests
├── pyproject.toml     # taskx configuration
└── requirements.txt   # Dependencies
```

## Available Tasks

Run `taskx list` to see all available tasks and their dependencies.
"""

        # requirements.txt stub
        files[
            "requirements.txt"
        ] = f"""# Core dependencies
numpy>=1.24.0
pandas>=2.0.0
scikit-learn>=1.3.0
jupyter>=1.0.0
jupyterlab>=4.0.0
matplotlib>=3.7.0
seaborn>=0.12.0

# ML framework
{"torch>=2.0.0" if ml_framework == "pytorch" else ""}
{"tensorflow>=2.13.0" if ml_framework == "tensorflow" else ""}

# Experiment tracking
{"mlflow>=2.7.0" if variables.get("use_mlflow", "True") == "True" else ""}

# Testing
pytest>=7.0.0
pytest-cov>=4.0.0

# Code quality
ruff>=0.1.0
mypy>=1.0.0
black>=23.0.0
"""

        return files
