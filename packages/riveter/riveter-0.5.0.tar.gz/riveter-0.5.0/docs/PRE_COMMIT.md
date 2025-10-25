# Pre-commit Hooks Setup Guide

This document explains how to set up and use pre-commit hooks for the Riveter project to maintain code quality and catch issues before they reach CI.

## Quick Setup

The fastest way to get started:

```bash
# Run the automated setup script
./setup-pre-commit.sh
```

This script will:
- Install pre-commit if not already installed
- Install the git hook scripts
- Run hooks on all files to check current state

## Manual Setup

If you prefer to set up manually:

```bash
# 1. Install pre-commit
pip install pre-commit

# 2. Install the git hooks
pre-commit install

# 3. (Optional) Run on all files to check current state
pre-commit run --all-files
```

## What the Hooks Do

Our pre-commit configuration includes the following checks:

### Code Quality Checks
- **trailing-whitespace**: Removes trailing whitespace
- **end-of-file-fixer**: Ensures files end with a newline
- **check-yaml**: Validates YAML syntax
- **check-added-large-files**: Prevents committing large files
- **check-merge-conflict**: Detects merge conflict markers
- **debug-statements**: Finds Python debug statements

### Code Formatting
- **Black**: Formats Python code consistently (line length: 100)
- **isort**: Sorts and organizes imports

### Code Analysis
- **Ruff**: Fast Python linter (replaces flake8, pylint, etc.)
- **MyPy**: Type checking for source code (src/ only, not tests/)

### Testing
- **pytest**: Runs the full test suite

## Using the Makefile

We provide a Makefile with convenient commands:

```bash
# Run all quality checks (like CI)
make all

# Individual commands
make format      # Format code with black + isort
make lint        # Run ruff linting
make type-check  # Run mypy type checking
make test        # Run pytest
make pre-commit  # Run all pre-commit hooks

# Setup
make setup-hooks # Install pre-commit hooks
make install-dev # Install development dependencies
```

## Configuration Files

### Full Configuration (`.pre-commit-config.yaml`)
The default configuration includes all checks and is designed to match the CI pipeline exactly.

### Simplified Configuration (`.pre-commit-config-simple.yaml`)
A lighter version with just essential checks:
- Basic file checks
- Black formatting
- Ruff linting (with auto-fix)

To use the simplified version:
```bash
cp .pre-commit-config-simple.yaml .pre-commit-config.yaml
pre-commit install
```

## How It Works

### Automatic Execution
Once installed, the hooks run automatically on every `git commit`:

```bash
git add .
git commit -m "Your commit message"
# Hooks run automatically here
```

### Manual Execution
You can also run hooks manually:

```bash
# Run all hooks on staged files
pre-commit run

# Run all hooks on all files
pre-commit run --all-files

# Run specific hook
pre-commit run black
pre-commit run mypy
pre-commit run pytest
```

### Bypassing Hooks
If you need to commit without running hooks (not recommended):

```bash
git commit --no-verify -m "Emergency commit"
```

## Troubleshooting

### Hook Failures
If a hook fails:

1. **Formatting hooks (black, isort)**: These auto-fix issues. Just add the changes and commit again:
   ```bash
   git add .
   git commit -m "Your message"
   ```

2. **Linting hooks (ruff)**: Fix the reported issues manually or use auto-fix:
   ```bash
   ruff check src/ tests/ --fix
   ```

3. **Type checking (mypy)**: Fix type annotations in your code

4. **Tests (pytest)**: Fix failing tests before committing

### Performance
If hooks are slow:
- Use the simplified configuration
- Run specific hooks: `pre-commit run black` instead of all hooks
- Skip tests for quick commits: comment out the pytest hook temporarily

### Updating Hooks
Keep hooks up to date:

```bash
pre-commit autoupdate
```

### Clean Cache
If you encounter issues:

```bash
pre-commit clean
pre-commit install --install-hooks
```

## Integration with IDEs

### VS Code
Install these extensions for the best experience:
- Python
- Black Formatter
- Ruff
- Pylance (for type checking)

Configure VS Code to format on save:
```json
{
    "python.formatting.provider": "black",
    "python.linting.enabled": true,
    "python.linting.ruffEnabled": true,
    "editor.formatOnSave": true
}
```

### PyCharm
- Enable Black as the code formatter
- Configure Ruff as an external tool
- Enable type checking with mypy

## Best Practices

1. **Run hooks before pushing**: Even though they run on commit, run `pre-commit run --all-files` before pushing to catch any issues

2. **Fix issues incrementally**: Don't let linting issues accumulate. Fix them as you go

3. **Use the Makefile**: The `make all` command runs the same checks as CI

4. **Keep dependencies updated**: Regularly run `pre-commit autoupdate`

5. **Customize for your workflow**: Use the simplified config if the full version is too strict

## CI Integration

The pre-commit hooks are designed to match the GitHub Actions CI pipeline exactly. If your code passes pre-commit hooks locally, it should pass CI.

The CI runs:
- Ruff linting
- Black formatting check
- MyPy type checking
- Pytest with coverage

## Getting Help

If you encounter issues:

1. Check this documentation
2. Run `pre-commit --help` for command help
3. Check the [pre-commit documentation](https://pre-commit.com/)
4. Ask in the project's issue tracker

## Example Workflow

Here's a typical development workflow with pre-commit:

```bash
# 1. Make your changes
vim src/riveter/new_feature.py

# 2. Run tests to make sure everything works
make test

# 3. Format and check your code
make format
make lint

# 4. Commit (hooks run automatically)
git add .
git commit -m "Add new feature"

# 5. If hooks fail, fix issues and try again
# (formatting hooks auto-fix, others need manual fixes)
git add .
git commit -m "Add new feature"

# 6. Push when ready
git push
```

This ensures your code is always in good shape and CI will pass!
