# Workflow Dependencies Documentation

This document provides comprehensive documentation for all dependencies used in the release workflow, including their purposes, version requirements, and maintenance procedures.

## Overview

The release workflow relies on several external Python packages to perform validation, building, security scanning, and publishing operations. This document serves as the centralized specification for all workflow dependencies.

### Critical Dependency Fix (2024-10-23)

**Issue**: The release workflow was failing during the "Install validation dependencies" step due to an incorrect package name.

**Problem**: The workflow specified `tomllib-w` (incorrect) instead of `tomli-w` (correct).

**Root Cause**: Naming confusion between:
- `tomllib`: Built-in Python 3.11+ module for reading TOML files
- `tomli-w`: Third-party PyPI package for writing TOML files
- `tomllib-w`: Non-existent package (incorrect combination)

**Resolution**:
- Corrected package name from `tomllib-w` to `tomli-w` in `.github/workflows/release.yml`
- Implemented dependency validation script to prevent future naming errors
- Added comprehensive documentation and troubleshooting guides
- Established centralized dependency management system

**Impact**: This fix ensures the release workflow can successfully install all required dependencies and complete the release process without interruption.

**Prevention**: Always run `python scripts/validate_dependencies.py` before committing workflow changes to catch package naming errors early.

## Dependency Specification

### Validation Dependencies

These dependencies are installed during the validation phase to check prerequisites and validate the release.

#### requests
- **Version**: `>=2.25.0`
- **Purpose**: HTTP requests for API validation and PyPI interaction
- **Python Compatibility**: Python 3.9+
- **Installation Step**: Install validation dependencies
- **Usage**:
  - Validating PyPI API responses
  - Checking package availability
  - Verifying release information
- **Security Considerations**: Always use HTTPS; validate SSL certificates
- **Latest Stable**: 2.32.5 (as of validation)

#### tomli-w
- **Version**: `>=1.0.0`
- **Purpose**: Writing TOML files for configuration updates (pyproject.toml)
- **Python Compatibility**: Python 3.9+
- **Installation Step**: Install validation dependencies
- **Usage**:
  - Updating version numbers in pyproject.toml
  - Modifying TOML configuration files
- **Note**: For reading TOML files, use built-in `tomllib` (Python 3.11+)
- **Security Considerations**: Validate TOML structure before writing
- **Latest Stable**: 1.2.0 (as of validation)

**Important**: The correct package name is `tomli-w` (with hyphen), not `tomllib-w`. The built-in Python module for reading TOML is `tomllib` (Python 3.11+), while `tomli-w` is the third-party package for writing TOML files.

### Build Dependencies

These dependencies are used to build the Python package distributions.

#### build
- **Version**: Latest stable
- **Purpose**: Building Python packages (source distribution and wheel)
- **Python Compatibility**: Python 3.9+
- **Installation Step**: Install build dependencies
- **Usage**:
  - Creating source distributions (sdist)
  - Building wheel distributions
- **Security Considerations**: Always validate built packages with twine
- **Latest Stable**: 1.3.0 (as of validation)

#### twine
- **Version**: Latest stable
- **Purpose**: Uploading packages to PyPI and validating distributions
- **Python Compatibility**: Python 3.9+
- **Installation Step**: Install build dependencies
- **Usage**:
  - Validating package integrity (`twine check`)
  - Uploading packages to PyPI
  - Verifying package metadata
- **Security Considerations**:
  - Use API tokens, never passwords
  - Store tokens in GitHub Secrets
  - Use `--non-interactive` flag in CI/CD
- **Latest Stable**: 6.2.0 (as of validation)

#### wheel
- **Version**: Latest stable
- **Purpose**: Building wheel distributions
- **Python Compatibility**: Python 3.8+
- **Installation Step**: Install build dependencies
- **Usage**:
  - Creating binary wheel distributions
  - Supporting package installation
- **Security Considerations**: Validate wheel contents before distribution
- **Latest Stable**: 0.45.1 (as of validation)

#### setuptools
- **Version**: Latest stable
- **Purpose**: Package building and installation utilities
- **Python Compatibility**: Python 3.9+
- **Installation Step**: Install build dependencies
- **Usage**:
  - Supporting package metadata
  - Providing build utilities
  - Managing package dependencies
- **Security Considerations**: Keep updated for security patches
- **Latest Stable**: 80.9.0 (as of validation)

### Security and Quality Tools

These dependencies are used for security scanning and code quality checks.

#### bandit
- **Version**: `>=1.7.0`
- **Purpose**: Security vulnerability scanning for Python code
- **Python Compatibility**: Python 3.9+
- **Installation Step**: Install security and quality tools
- **Usage**:
  - Scanning source code for security issues
  - Identifying common security vulnerabilities
  - Generating security reports
- **Security Considerations**: Review all findings before release
- **Latest Stable**: 1.8.6 (as of validation)

#### safety
- **Version**: Latest stable
- **Purpose**: Checking dependencies for known security vulnerabilities
- **Python Compatibility**: Python 3.8+
- **Installation Step**: Install security and quality tools
- **Usage**:
  - Scanning dependencies for CVEs
  - Checking against vulnerability databases
  - Generating vulnerability reports
- **Security Considerations**:
  - Run before every release
  - Address all critical vulnerabilities
  - Keep vulnerability database updated
- **Latest Stable**: 3.6.2 (as of validation)

## Dependency Management Best Practices

### Centralized Dependency Management

All workflow dependencies are managed through a centralized system to ensure consistency and prevent errors:

1. **Single Source of Truth**: `.github/workflow-dependencies.yml`
   - Contains all dependency specifications
   - Documents purpose and requirements for each package
   - Tracks version compatibility and update history

2. **Automated Validation**: `scripts/validate_dependencies.py`
   - Verifies package names against PyPI
   - Checks version compatibility
   - Validates Python version requirements
   - Runs automatically in workflow

3. **Documentation**: This file and related docs
   - Comprehensive dependency documentation
   - Troubleshooting guides
   - Update procedures

### Version Pinning Strategy

1. **Critical Dependencies**: Pin to specific versions for reproducibility
   - Example: `requests==2.32.5`
   - Use when stability is critical
   - Recommended for: validation dependencies, build tools

2. **Flexible Dependencies**: Use minimum version constraints
   - Example: `tomli-w>=1.0.0`
   - Use when compatibility is more important than exact versions
   - Recommended for: utility packages, optional features

3. **Latest Dependencies**: Use latest for tools that need frequent updates
   - Example: `safety` (security database updates)
   - Use for security and quality tools
   - Recommended for: security scanners, linters

### Dependency Naming Guidelines

To avoid naming errors like the `tomllib-w` vs `tomli-w` issue:

1. **Always verify package names on PyPI** before adding to workflow
   ```bash
   # Check package exists
   pip index versions {package-name}
   # Or
   curl https://pypi.org/pypi/{package-name}/json
   ```

2. **Distinguish between built-in and third-party packages**:
   - Built-in modules (Python 3.11+): `tomllib`, `json`, `pathlib`, `sys`
   - Third-party packages (PyPI): `tomli-w`, `requests`, `twine`, `build`

3. **Watch for common naming patterns**:
   - Hyphens vs underscores: Import uses `_`, install uses `-`
   - Example: `pip install tomli-w` → `import tomli_w`

4. **Use validation script** to catch errors:
   ```bash
   python scripts/validate_dependencies.py --verbose --fail-on-warnings
   ```

### Validation Procedures

Before adding or updating any workflow dependency:

1. **Verify Package Existence**
   ```bash
   python scripts/validate_dependencies.py --verbose
   ```

2. **Check Python Compatibility**
   - Ensure package supports Python 3.12+
   - Test on all target Python versions

3. **Security Review**
   - Check package maintainer reputation
   - Review package dependencies
   - Scan for known vulnerabilities

4. **Test Integration**
   - Test in isolated environment
   - Verify workflow functionality
   - Check for conflicts with existing dependencies

### Upgrade Procedures

When upgrading workflow dependencies:

1. **Check Release Notes**
   - Review changelog for breaking changes
   - Identify new features or deprecations
   - Note security fixes

2. **Test in Isolation**
   ```bash
   # Create test environment
   python -m venv test_env
   source test_env/bin/activate

   # Install new version
   pip install package_name==new_version

   # Run validation
   python scripts/validate_dependencies.py
   ```

3. **Update Documentation**
   - Update version numbers in this document
   - Document any breaking changes
   - Update usage examples if needed

4. **Test Workflow**
   - Run workflow in dry-run mode
   - Verify all steps complete successfully
   - Check for deprecation warnings

5. **Commit Changes**
   - Update workflow files
   - Update documentation
   - Create pull request with changes

### Maintenance Schedule

- **Monthly**: Check for security updates
- **Quarterly**: Review and update all dependencies
- **Annually**: Major version upgrades and compatibility review

## Troubleshooting

### Common Issues

#### Package Not Found on PyPI

**Symptom**: `pip install` fails with "No matching distribution found"

**Example Error**:
```
ERROR: Could not find a version that satisfies the requirement tomllib-w
ERROR: No matching distribution found for tomllib-w
```

**Causes**:
- Incorrect package name (e.g., `tomllib-w` instead of `tomli-w`)
- Package removed from PyPI
- Typo in package name
- Confusion between built-in modules and PyPI packages

**Resolution**:
1. Verify package name on PyPI: https://pypi.org/
   ```bash
   # Check if package exists
   curl -s https://pypi.org/pypi/{package-name}/json | jq '.info.name'
   ```

2. Run validation script:
   ```bash
   python scripts/validate_dependencies.py --verbose
   ```

3. Check for common naming mistakes:
   - `tomllib-w` ❌ → `tomli-w` ✅
   - Underscores vs hyphens: `package_name` vs `package-name`
   - Plural vs singular: `requests` vs `request`

4. Distinguish between built-in and third-party:
   - Built-in (no install needed): `tomllib`, `json`, `pathlib`
   - Third-party (install from PyPI): `tomli-w`, `requests`, `twine`

5. Update workflow with correct package name:
   ```yaml
   # In .github/workflows/release.yml
   - name: Install validation dependencies
     run: |
       pip install requests tomli-w  # Correct names
   ```

**Prevention**:
- Always validate dependencies before committing: `python scripts/validate_dependencies.py`
- Use the dependency validation script in pre-commit hooks
- Reference `.github/workflow-dependencies.yml` for canonical package names
- Test workflow changes in dry-run mode first

#### Version Compatibility Issues

**Symptom**: Package installs but fails at runtime

**Causes**:
- Python version incompatibility
- Conflicting dependency versions
- Breaking changes in new version

**Resolution**:
1. Check package Python version requirements
2. Review package changelog for breaking changes
3. Pin to last known working version
4. Test in isolated environment

#### Security Vulnerabilities

**Symptom**: Safety or Bandit reports vulnerabilities

**Causes**:
- Outdated package versions
- Known CVEs in dependencies
- Insecure code patterns

**Resolution**:
1. Review vulnerability details
2. Update to patched version if available
3. Consider alternative packages if no fix available
4. Document risk acceptance if upgrade not possible

## Validation Script

The `scripts/validate_dependencies.py` script provides automated validation of all workflow dependencies.

### Usage

```bash
# Basic validation
python scripts/validate_dependencies.py

# Verbose output
python scripts/validate_dependencies.py --verbose

# Check specific Python versions
python scripts/validate_dependencies.py --python-versions 3.12 3.13

# Fail on warnings
python scripts/validate_dependencies.py --fail-on-warnings

# JSON output
python scripts/validate_dependencies.py --json-output
```

### Integration

The validation script is integrated into the release workflow to ensure all dependencies are valid before proceeding with the release.

## Security Considerations

### Token Management

- **PyPI Tokens**: Store in GitHub Secrets as `PYPI_API_TOKEN`
- **Token Format**: Must start with `pypi-`
- **Token Scope**: Use project-specific tokens with upload-only permissions
- **Token Rotation**: Rotate every 90 days

### Dependency Security

- **Source Verification**: Only install from PyPI
- **Checksum Validation**: Verify package integrity
- **Vulnerability Scanning**: Run safety checks before every release
- **Minimal Dependencies**: Only include necessary packages

### Network Security

- **HTTPS Only**: All package downloads use HTTPS
- **Certificate Validation**: Always validate SSL certificates
- **Timeout Configuration**: Set reasonable timeouts for network operations

## Dependency Update Helper

A helper script is available to assist with dependency updates:

```bash
# Check for updates
python scripts/update_dependency.py requests --check-only

# Test update with all Python versions
python scripts/update_dependency.py requests --verbose

# Test specific version
python scripts/update_dependency.py requests --test-version 2.33.0 --verbose

# Dry run to see what would happen
python scripts/update_dependency.py requests --dry-run
```

For detailed update procedures, see [Dependency Update Procedures](./DEPENDENCY_UPDATE_PROCEDURES.md).

## References

- [PyPI Package Index](https://pypi.org/)
- [Python Packaging Guide](https://packaging.python.org/)
- [Twine Documentation](https://twine.readthedocs.io/)
- [Security Best Practices](../docs/SECURITY_SETUP.md)
- [Dependency Update Procedures](./DEPENDENCY_UPDATE_PROCEDURES.md)

## Changelog

### 2024-10-23
- Initial documentation created
- Added comprehensive dependency specifications
- Documented validation and upgrade procedures
- Fixed `tomllib-w` → `tomli-w` naming issue
