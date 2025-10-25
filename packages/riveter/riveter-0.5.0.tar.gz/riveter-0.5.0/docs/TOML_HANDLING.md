# TOML File Handling

This document describes the TOML file handling implementation in Riveter, including reading, writing, validation, and error recovery mechanisms.

## Overview

Riveter uses a robust TOML handling system that:
- Uses `tomllib` (Python 3.11+ built-in) for reading TOML files
- Uses `tomli-w` for writing TOML files
- Provides structure validation
- Implements error handling and recovery
- Preserves formatting where possible

## Components

### TOMLHandler Class

The `TOMLHandler` class (`src/riveter/toml_handler.py`) provides comprehensive TOML file operations:

```python
from riveter.toml_handler import TOMLHandler
from pathlib import Path

# Initialize handler
handler = TOMLHandler(Path('pyproject.toml'))

# Read TOML file
data = handler.read()

# Get specific values using dot notation
version = handler.get_value('project.version')

# Set values
handler.set_value('project.version', '1.0.0')

# Write with formatting preservation
handler.write(data, preserve_formatting=True)

# Validate structure
handler.validate_structure(required_keys=['project.name', 'project.version'])
```

### Features

#### 1. Reading TOML Files

Uses Python's built-in `tomllib` (Python 3.11+) for parsing:

```python
handler = TOMLHandler(Path('pyproject.toml'))
data = handler.read()  # Returns dict
```

Error handling:
- `TOMLReadError`: Raised when file cannot be read or parsed
- Stores original content for potential recovery
- Provides detailed error messages

#### 2. Writing TOML Files

Uses `tomli-w` for writing TOML files:

```python
handler.write(data, preserve_formatting=True)
```

Features:
- Automatic backup creation before writing
- Formatting preservation for simple updates
- Verification after write
- Automatic rollback on failure

#### 3. Structure Validation

Validates TOML file structure and required fields:

```python
handler.validate_structure(required_keys=[
    'project.name',
    'project.version',
    'project.description'
])
```

#### 4. Error Recovery

Built-in error recovery mechanisms:
- Automatic backup creation
- Restore from backup on failure
- Verification after modifications

### Validation Script

The `scripts/validate_toml.py` script provides command-line TOML validation:

```bash
# Validate pyproject.toml
python scripts/validate_toml.py pyproject.toml --type pyproject --verbose

# Validate with custom required keys
python scripts/validate_toml.py config.toml --required-keys section.key1 section.key2

# Fail on warnings
python scripts/validate_toml.py file.toml --fail-on-warnings
```

Validation checks:
- File existence and readability
- TOML syntax correctness
- UTF-8 encoding
- Required keys presence
- Structure integrity
- Empty tables detection

## Integration with Version Manager

The `VersionManager` class uses `TOMLHandler` for all TOML operations:

```python
from riveter.version_manager import VersionManager, VersionType

vm = VersionManager()

# Read current version (uses TOMLHandler internally)
current = vm.read_current_version()

# Update version (uses TOMLHandler with backup/restore)
vm.update_pyproject_version('1.0.0')
```

Benefits:
- Consistent TOML handling across the codebase
- Automatic backup and recovery
- Formatting preservation
- Robust error handling

## Workflow Integration

The release workflow uses TOML operations in several places:

### 1. Version Reading

```yaml
- name: Extract current version
  run: |
    current_version=$(python -c "
    import tomllib
    with open('pyproject.toml', 'rb') as f:
        data = tomllib.load(f)
    print(data['project']['version'])
    ")
```

### 2. Version Writing

```yaml
- name: Update version in pyproject.toml
  run: |
    python -c "
    import tomllib
    import tomli_w

    # Read, update, write with backup
    with open('pyproject.toml', 'rb') as f:
        data = tomllib.load(f)

    data['project']['version'] = '$new_version'

    with open('pyproject.toml', 'wb') as f:
        tomli_w.dump(data, f)
    "
```

### 3. TOML Validation

```yaml
- name: Validate TOML files
  run: |
    python scripts/validate_toml.py pyproject.toml --type pyproject --verbose
```

### 4. Post-Modification Validation

```yaml
- name: Validate after update
  run: |
    python scripts/validate_toml.py pyproject.toml --type pyproject --verbose
```

## Error Handling

### Exception Hierarchy

```
TOMLError (base)
├── TOMLReadError
├── TOMLWriteError
└── TOMLValidationError
```

### Error Recovery

1. **Backup Creation**: Automatic backup before modifications
2. **Verification**: Validate changes after write
3. **Rollback**: Restore from backup on failure
4. **Clear Messages**: Detailed error messages with context

Example:

```python
try:
    handler = TOMLHandler(Path('pyproject.toml'))
    handler.read()
    handler.backup()  # Create backup

    handler.set_value('project.version', '1.0.0')
    handler.write(handler._parsed_data)

    # Verify
    handler.read()
    if handler.get_value('project.version') != '1.0.0':
        handler.restore_from_backup()

except TOMLError as e:
    print(f"TOML operation failed: {e}")
    # Backup is automatically restored
```

## Best Practices

1. **Always use TOMLHandler**: Don't parse TOML files manually
2. **Validate after modifications**: Use validation script or `validate_structure()`
3. **Use dot notation**: Access nested keys with `get_value('section.key')`
4. **Enable formatting preservation**: Use `preserve_formatting=True` when possible
5. **Handle exceptions**: Catch specific TOML exceptions for better error handling

## Testing

Test TOML operations:

```bash
# Test reading
python -c "from riveter.toml_handler import TOMLHandler; \
           h = TOMLHandler('pyproject.toml'); \
           print(h.read())"

# Test validation
python scripts/validate_toml.py pyproject.toml --type pyproject -v

# Test version manager
python -c "from riveter.version_manager import VersionManager; \
           vm = VersionManager(); \
           print(vm.read_current_version())"
```

## Dependencies

- **tomllib**: Python 3.11+ built-in (reading)
- **tomli-w**: PyPI package (writing) - `pip install tomli-w`

## See Also

- [Workflow Dependencies](WORKFLOW_DEPENDENCIES.md)
- [Release Workflow](RELEASE_WORKFLOW.md)
- [Version Management](../src/riveter/version_manager.py)
