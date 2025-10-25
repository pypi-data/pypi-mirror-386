# Changelog

All notable changes to taskx will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.0] - 2025-TBD

### Added

#### Shell Completion
- **TAB completion for bash, zsh, fish, and PowerShell** (#1)
  - Install with `taskx completion <shell> --install`
  - Context-aware completion for commands, tasks, and options
  - Dynamic task name loading from current `pyproject.toml`
  - Complete graph formats (`tree`, `dot`, `mermaid`)
  - Complete `.toml` files for `--config` option
  - Smart completion after `run`, `watch`, `graph` commands
  - Automatic installation to system completion directories
  - Works with both `taskx` and `python -m taskx` invocations

#### Task Aliases
- **Global aliases for tasks** (#2)
  - Define short names in `[tool.taskx.aliases]` section
  - Example: `t = "test"` allows `taskx run t`
  - Alias resolution shown during execution
  - Automatic conflict detection with reserved names
  - Validation prevents duplicate aliases
  - Support for per-task aliases in task definitions
  - Aliases included in shell completion
  - `--include-aliases` flag for `taskx list` command

#### Interactive Prompts
- **User input during task execution** (#3)
  - Four prompt types: `text`, `select`, `confirm`, `password`
  - Configure prompts in task definitions: `prompt.<VAR> = {...}`
  - Default values for non-interactive mode (CI/CD compatible)
  - Environment variable overrides via `--env` flag
  - Variable expansion in commands using `${VAR}` syntax
  - Confirmation dialogs with `confirm` field
  - Variable expansion in confirmation messages
  - Safe password input (hidden characters)
  - Automatic non-interactive mode detection
  - Proper KeyboardInterrupt handling

#### Project Templates
- **Production-ready project templates** (#4)
  - Django web application template with migrations, testing, deployment
  - FastAPI microservice template with async support and Docker
  - Data Science / ML project template with Jupyter, MLflow, pipelines
  - Python library template with PyPI publishing workflow
  - Interactive template customization via prompts
  - List templates with `taskx init --list-templates`
  - Create projects with `taskx init --template <name>`
  - Jinja2 template rendering with sandboxed environment
  - Template-specific prompts and customization
  - Best-practice task configurations included
  - Docker, Celery, database support options

### Changed

- Enhanced `taskx list` command with new flags
  - `--names-only`: Output only task names (one per line) for shell completion
  - `--include-aliases`: Include aliases in output
- Improved `taskx init` command
  - `--template` flag to use project templates
  - `--list-templates` flag to show available templates
  - Better interactive prompts for template customization
- Updated CLI with improved error messages and user feedback
- Enhanced configuration validation for new features
- Improved path handling in `--config` option (now accepts non-existent paths for `init`)

### Fixed

- Fixed Click Path validation issue preventing `taskx init` from creating configs
  - Changed `type=click.Path()` to `type=click.Path(exists=False)` in main CLI
- Improved error messages for configuration errors
- Better handling of non-interactive environments
- Enhanced cross-platform compatibility

### Security

- **Sandboxed Jinja2 template rendering** to prevent code injection
  - Uses `jinja2.sandbox.SandboxedEnvironment`
  - Restricts available functions and methods
  - Safe template variable expansion
- Input validation for aliases and task names
  - Reserved name validation
  - Duplicate alias detection
  - Invalid character prevention
- Secure password prompt handling
  - Hidden input during password collection
  - No echo to terminal

### Documentation

- Added comprehensive feature guides:
  - [Shell Completion Guide](./docs/shell-completion.md) - Installation and usage for all shells
  - [Task Aliases Guide](./docs/task-aliases.md) - Global and per-task aliases
  - [Interactive Prompts Guide](./docs/interactive-prompts.md) - All prompt types and CI/CD compatibility
  - [Project Templates Guide](./docs/project-templates.md) - Available templates and customization
- Added [Migration Guide](./docs/migration-v0.1.0-to-v0.2.0.md) for v0.1.0 users
- Updated README.md with v0.2.0 features
- Added release notes for v0.2.0

### Testing

- Added comprehensive test suite for new features:
  - Completion generator tests (bash, zsh, fish, powershell)
  - Alias resolution and validation tests
  - Interactive prompt tests (all types)
  - Template generation tests (all templates)
  - Integration tests for new CLI commands
  - Performance tests and benchmarks
  - Memory profiling tests
- Achieved 70% test coverage (baseline established)
- Added CI/CD testing for multiple Python versions (3.8-3.12)

### Internal

- Refactored completion system with abstract base class
  - `CompletionGenerator` base class for all shells
  - Consistent API across all completion generators
  - Easy to add new shell support
- Improved configuration loading and validation
  - `ConfigError` exception for better error handling
  - Enhanced TOML parsing with better error messages
  - Alias validation during config load
- New prompt management system
  - `PromptManager` class for consistent prompt handling
  - `PromptConfig` and `ConfirmConfig` dataclasses
  - Non-interactive mode detection
  - Environment variable override support
- Template system architecture
  - Abstract `Template` base class
  - Template registry for easy discovery
  - Jinja2 integration with sandboxing
  - Variable validation and expansion

## [0.1.0] - 2025-01-15

### Added

- Initial release of taskx
- **Core task execution engine**
  - Run tasks defined in `pyproject.toml`
  - Simple string commands: `task = "command"`
  - Complex task definitions with dependencies, environment variables
- **Task dependencies**
  - Serial dependencies with `depends = ["task1", "task2"]`
  - Parallel execution with `parallel = ["task1", "task2"]`
  - Automatic dependency resolution and cycle detection
- **Watch mode** with file monitoring
  - `taskx watch <task>` to run on file changes
  - Configure watched files with `watch = ["pattern"]`
  - Debouncing to prevent duplicate runs
- **Environment variable support**
  - Global env vars in `[tool.taskx.env]`
  - Per-task env vars with `env = {...}`
  - Variable expansion with `${VAR}` syntax
  - CLI override with `--env KEY=VALUE`
- **Lifecycle hooks**
  - `pre` - Run before task
  - `post` - Run after task
  - `on_error` - Run on task failure
  - `on_success` - Run on task success
- **Dependency graph visualization**
  - `taskx graph` command
  - Multiple output formats: tree, dot, mermaid
  - Task filtering with `--task` option
- **Multi-layer security validation**
  - Command injection prevention
  - Path traversal protection
  - Input validation
- **Cross-platform support**
  - Works on Windows, macOS, Linux
  - Shell-agnostic task execution
  - Proper path handling for all platforms
- **CLI commands**
  - `taskx list` - List all tasks
  - `taskx run <task>` - Run a task
  - `taskx watch <task>` - Watch and run on changes
  - `taskx graph` - Show dependency graph
  - `taskx init` - Initialize configuration
  - `taskx --version` - Show version
- **Rich terminal output**
  - Color-coded output with emoji indicators
  - Progress indication for running tasks
  - Task timing and performance metrics
  - Formatted error messages

### Dependencies

- click >= 8.0.0 - CLI framework
- rich >= 13.0.0 - Rich terminal output
- tomli >= 2.0.0 (Python < 3.11) - TOML parsing
- watchfiles >= 0.18.0 - File watching
- questionary >= 2.0.0 - Interactive prompts (v0.2.0)
- python-dotenv >= 1.0.0 - Environment variable loading
- jinja2 >= 3.1.0 - Template rendering (v0.2.0)

## Links

- [Homepage](https://github.com/0xV8/taskx)
- [Documentation](https://github.com/0xV8/taskx/tree/main/docs)
- [Issue Tracker](https://github.com/0xV8/taskx/issues)

---

## Version History Summary

- **v0.2.0** (Current) - Shell Completion, Aliases, Prompts, Templates
- **v0.1.0** - Initial Release - Core Task Runner

---

**Legend:**
- `Added` - New features
- `Changed` - Changes in existing functionality
- `Deprecated` - Soon-to-be removed features
- `Removed` - Removed features
- `Fixed` - Bug fixes
- `Security` - Security improvements
