# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Log Time to Tempo is a Python CLI application for logging work time to JIRA/Tempo from the command line. It provides commands for time tracking, statistics, and project management with self-hosted JIRA instances.

## Development Commands

### Essential Development Workflow
```bash
# Fix linting and formatting issues
just fix

# Run linting checks
just lint

# Run tests (66 tests, completes in 3-5 seconds)
just test

# Run tests with coverage
just cov

# Build the package
just build

# Release new version (includes testing, tagging, building, publishing)
just release
```

### Testing CLI Functionality
```bash
# Test non-JIRA commands (safe to run without network)
uv run lt --help
uv run lt config --help
uv run lt alias --help
uv run lt --version

# JIRA-dependent commands (require network connection)
# These will prompt for token or fail without JIRA access:
# uv run lt log --help
# uv run lt stats --help
# uv run lt init --help
```

## Architecture

### Core Components
- **CLI Interface** (`src/log_time_to_tempo/cli/main.py`): Main entry point using Typer with command groups (Configuration, POST, GET)
- **JIRA Integration** (`src/log_time_to_tempo/_jira.py`): Wrapper around JIRA Python API for project/issue management
- **Tempo Integration** (`src/log_time_to_tempo/tempo.py`): REST API client for Tempo Timesheets worklog operations
- **Caching System** (`src/log_time_to_tempo/caching.py`): Local file-based caching for projects and issues
- **Configuration** (`src/log_time_to_tempo/cli/config.py`): Hierarchical config management (system-wide and per-directory)

### Key Command Categories
- **Configuration Commands**: `config`, `alias`, `reset` - Work offline
- **POST Commands**: `log`, `logm` - Create worklogs (require JIRA)
- **GET Commands**: `stats`, `list`, `issues`, `projects`, `budget` - Read data (require JIRA)

### Sparkline Visualization
- **Axis System**: Smart axis labeling based on date range (monthly/weekly/yearly)
- **Visualization**: Daily time patterns shown in `stats` command using sparklines
- **Implementation**: `src/log_time_to_tempo/cli/_sparkline.py` handles axis generation and visualization

## Development Guidelines

### Adding New Commands
1. Add command function to `src/log_time_to_tempo/cli/main.py`
2. Use `@app.command()` decorator with appropriate `rich_help_panel`
3. Follow existing patterns for option/argument definitions
4. Add tests in `src/test_log_time_to_tempo/cli/`

### Code Quality Standards
- **Linting**: Uses `ruff` with auto-fix capabilities
- **Formatting**: `ruff format` with 100 char line length, single quotes
- **Docstrings**: `docformatter` for consistent documentation
- **Testing**: pytest with coverage reporting

### Dependencies and Environment
- **Package Manager**: `uv` for dependency management and virtual environments
- **Task Runner**: `just` for development commands
- **Python Version**: 3.11+ required
- **CLI Entry Points**: `lt`, `log-time`, `log-time-to-tempo`

## Configuration System

### Environment Variables
- `JIRA_API_TOKEN`: JIRA personal access token
- `JIRA_INSTANCE`: JIRA server URL
- `LT_*`: Application-specific configuration options

### Configuration Hierarchy
- **System-wide**: `lt config --system KEY VALUE`
- **Local directory**: `lt config KEY VALUE` (applies to current directory and subdirectories)

## Testing Strategy

- **Unit Tests**: Mock JIRA/Tempo APIs for CLI commands
- **Integration Tests**: Use `TestClient` mock for JIRA interactions
- **Performance**: All tests complete in <5 seconds
- **Coverage**: XML and HTML coverage reports generated
- **Testing Guidelines**:
  - Always extend existing test cases to cover new features
  - Never write ad-hoc tests when validating features
  - Update tests to verify new functionality while maintaining backward compatibility

## Performance Expectations

- **Setup**: <5 seconds for initial uv install
- **Linting**: <1 second
- **Testing**: 3-4 seconds (66 tests)
- **Building**: <1 second
- **CLI Startup**: <1 second for non-JIRA commands

**Important**: Never cancel development commands - they complete very quickly.