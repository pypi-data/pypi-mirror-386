# GitHub Workflows and Configuration

This directory contains GitHub Actions workflows and related configuration files for the Riveter project.

## Workflows

### release.yml
Automated release workflow that handles:
- Version validation and bumping
- Comprehensive testing across multiple platforms and Python versions
- Security scanning
- Package building and validation
- Publishing to PyPI
- GitHub release creation

**Trigger**: Manual via workflow_dispatch
**Documentation**: See `docs/RELEASE_WORKFLOW.md`

## Configuration Files

### workflow-dependencies.yml
Centralized specification for all workflow dependencies. This file serves as the single source of truth for:
- Package names and versions
- Dependency purposes and requirements
- Python version compatibility
- Update and maintenance procedures
- Security considerations

**Purpose**: Ensure consistent and validated dependencies across all workflows
**Documentation**: See `docs/WORKFLOW_DEPENDENCIES.md`

## Dependency Management

### Overview
All workflow dependencies are centrally managed to ensure:
- Correct package names (e.g., `tomli-w` not `tomllib-w`)
- Version compatibility with Python 3.12+
- Security and stability
- Easy updates and maintenance

### Quick Commands

```bash
# Validate all dependencies
python scripts/validate_dependencies.py --verbose

# Check for updates
python scripts/update_dependency.py requests --check-only

# Test an update
python scripts/update_dependency.py requests --verbose
```

### Documentation
- **Quick Reference**: `docs/DEPENDENCY_QUICK_REFERENCE.md`
- **Full Documentation**: `docs/WORKFLOW_DEPENDENCIES.md`
- **Update Procedures**: `docs/DEPENDENCY_UPDATE_PROCEDURES.md`

### Key Files
- **Dependency Spec**: `.github/workflow-dependencies.yml`
- **Validation Script**: `scripts/validate_dependencies.py`
- **Update Helper**: `scripts/update_dependency.py`

## Workflow Dependencies

### Validation Phase
- **requests** (>=2.25.0): HTTP requests for API validation
- **tomli-w** (>=1.0.0): Writing TOML files for version updates

### Build Phase
- **build**: Building Python packages
- **twine**: Uploading to PyPI and validation
- **wheel**: Building wheel distributions
- **setuptools**: Package utilities

### Security Phase
- **bandit** (>=1.7.0): Security vulnerability scanning
- **safety**: Dependency vulnerability checking

## Maintenance

### Schedule
- **Monthly**: Security updates
- **Quarterly**: Dependency review
- **Annually**: Major version upgrades

### Update Process
1. Check for updates: `python scripts/update_dependency.py {package} --check-only`
2. Test update: `python scripts/update_dependency.py {package} --verbose`
3. Update documentation: Edit `workflow-dependencies.yml` and `docs/WORKFLOW_DEPENDENCIES.md`
4. Test workflow: Run in dry-run mode
5. Commit changes

See `docs/DEPENDENCY_UPDATE_PROCEDURES.md` for detailed procedures.

## Security

### Token Management
- **PYPI_API_TOKEN**: Stored in GitHub Secrets, project-specific, upload-only
- **GITHUB_TOKEN**: Automatically provided by GitHub Actions

### Best Practices
- Only install packages from PyPI
- Validate package names before installation
- Run security scans before every release
- Use HTTPS for all package downloads
- Pin critical dependencies for stability

See `docs/SECURITY_SETUP.md` for detailed security configuration.

## Troubleshooting

### Package Not Found

**Symptom**: Workflow fails during "Install validation dependencies" step with error like:
```
ERROR: Could not find a version that satisfies the requirement tomllib-w
ERROR: No matching distribution found for tomllib-w
```

**Root Cause**: Incorrect package name in workflow file. The correct package name is `tomli-w` (with hyphen), not `tomllib-w`.

**Background**:
- `tomllib` is a built-in Python 3.11+ module for reading TOML files
- `tomli-w` is a third-party PyPI package for writing TOML files
- Common mistake: mixing the names to create non-existent `tomllib-w`

**Resolution**:
```bash
# 1. Verify package name
python scripts/validate_dependencies.py --verbose

# 2. Check PyPI for correct package name
curl https://pypi.org/pypi/tomli-w/json

# 3. Update workflow file if needed
# In .github/workflows/release.yml:
# WRONG: pip install tomllib-w
# CORRECT: pip install tomli-w

# 4. Validate fix
python scripts/validate_dependencies.py --verbose
```

**Prevention**: Always run `python scripts/validate_dependencies.py` before committing workflow changes.

### Workflow Fails
```bash
# Check workflow logs
gh run list --workflow=release.yml

# Validate dependencies
python scripts/validate_dependencies.py --verbose

# Test in dry-run mode
gh workflow run release.yml -f version_type=patch -f dry_run=true
```

### Dependency Installation Failures

**Symptom**: Workflow fails with pip installation errors

**Common Causes**:
1. **Incorrect package name**: Verify against PyPI
2. **Version incompatibility**: Check Python version requirements
3. **Network issues**: Temporary PyPI outage
4. **Typo in workflow file**: Review recent changes

**Resolution Steps**:
```bash
# 1. Validate all dependencies
python scripts/validate_dependencies.py --verbose --fail-on-warnings

# 2. Test installation locally
python -m venv test_env
source test_env/bin/activate
pip install requests tomli-w  # Use exact workflow dependencies
deactivate
rm -rf test_env

# 3. Check package on PyPI
pip index versions {package-name}

# 4. Review workflow file
cat .github/workflows/release.yml | grep "pip install"
```

### TOML File Handling Issues

**Symptom**: Errors when reading or writing pyproject.toml

**Resolution**:
```bash
# Validate TOML structure
python scripts/validate_toml.py pyproject.toml --type pyproject --verbose

# Check TOML dependencies
# Reading: Uses built-in tomllib (Python 3.11+)
# Writing: Uses tomli-w package from PyPI

# Test TOML operations
python -c "
import tomllib
with open('pyproject.toml', 'rb') as f:
    data = tomllib.load(f)
print('✅ TOML reading works')
"
```

### Update Issues
```bash
# Rollback to previous version
git revert {commit}

# Document issue
# Edit workflow-dependencies.yml with notes

# Create tracking issue
gh issue create --title "Dependency issue: {package}"
```

### Dependency Validation Failures

**Symptom**: `validate_dependencies.py` script reports errors

**Resolution**:
```bash
# Run with verbose output
python scripts/validate_dependencies.py --verbose

# Check specific dependency
python -c "
import requests
response = requests.get('https://pypi.org/pypi/{package}/json')
print(f'Package exists: {response.status_code == 200}')
"

# Review dependency specification
cat .github/workflow-dependencies.yml
```

## References

- [Workflow Dependencies](../docs/WORKFLOW_DEPENDENCIES.md)
- [Dependency Update Procedures](../docs/DEPENDENCY_UPDATE_PROCEDURES.md)
- [Dependency Quick Reference](../docs/DEPENDENCY_QUICK_REFERENCE.md)
- [Security Setup](../docs/SECURITY_SETUP.md)
- [Release Workflow](../docs/RELEASE_WORKFLOW.md)

## Contributing

When modifying workflows or dependencies:
1. Test changes in dry-run mode
2. Update documentation
3. Run validation scripts
4. Create pull request with detailed description
5. Ensure all checks pass

---

**Last Updated**: 2024-10-23
