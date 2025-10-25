# Dependency Update Procedures

This document provides comprehensive procedures for updating workflow dependencies, including compatibility testing, upgrade paths, and rollback procedures.

## Overview

Workflow dependencies must be carefully managed to ensure release workflow stability and security. This document outlines the procedures for safely updating dependencies while maintaining compatibility and reliability.

## Update Process

### 1. Pre-Update Assessment

Before updating any dependency, perform the following assessment:

#### Check Current Status
```bash
# Validate current dependencies
python scripts/validate_dependencies.py --verbose

# Check for available updates
pip list --outdated
```

#### Review Release Notes
- Visit the package's PyPI page: `https://pypi.org/project/{package-name}/`
- Review the changelog for breaking changes
- Check for security advisories
- Note any deprecation warnings

#### Assess Impact
- Identify which workflow steps use the dependency
- Review code that imports or uses the package
- Check for version-specific features in use
- Evaluate compatibility with Python 3.12+

### 2. Testing in Isolation

Create an isolated test environment to validate the update:

```bash
# Create test environment
python -m venv test_dependency_update
source test_dependency_update/bin/activate  # On Windows: test_dependency_update\Scripts\activate

# Install current dependencies
pip install -r requirements.txt  # or pip install -e ".[dev]"

# Update specific package
pip install --upgrade {package-name}

# Run validation
python scripts/validate_dependencies.py --verbose

# Test functionality
pytest tests/ -v

# Deactivate and clean up
deactivate
rm -rf test_dependency_update
```

### 3. Compatibility Testing

Test the updated dependency across all supported Python versions:

```bash
# Test with Python 3.12
python3.12 -m venv test_py312
source test_py312/bin/activate
pip install {package-name}=={new-version}
python scripts/validate_dependencies.py
pytest tests/
deactivate

# Test with Python 3.13
python3.13 -m venv test_py313
source test_py313/bin/activate
pip install {package-name}=={new-version}
python scripts/validate_dependencies.py
pytest tests/
deactivate
```

### 4. Update Documentation

Update all relevant documentation:

#### Update workflow-dependencies.yml
```yaml
dependencies:
  {category}:
    packages:
      - name: {package-name}
        version: "{new-version-spec}"
        latest_tested: "{new-version}"
        purpose: "{description}"
        notes: |
          Updated on {date}: {reason for update}
          Breaking changes: {list any breaking changes}
```

#### Update WORKFLOW_DEPENDENCIES.md
```markdown
#### {package-name}
- **Version**: `{new-version-spec}`
- **Latest Stable**: {new-version} (as of {date})
- **Update Notes**: {description of changes}
```

### 5. Update Workflow Files

Update the dependency in workflow files:

```yaml
# .github/workflows/release.yml
- name: Install {category} dependencies
  run: |
    python -m pip install --upgrade pip
    pip install {package-name}=={new-version}  # Pin to specific version if critical
```

### 6. Validation and Testing

Run comprehensive validation:

```bash
# Validate TOML files
python scripts/validate_toml.py pyproject.toml --type pyproject --verbose

# Validate dependencies
python scripts/validate_dependencies.py --verbose --fail-on-warnings

# Run security scans
bandit -r src/ -f txt
safety check

# Run full test suite
pytest tests/ -v --cov=riveter --cov-report=term-missing

# Test CLI functionality
riveter --version
riveter scan -r examples/rules/basic_rules.yml -t examples/terraform/simple.tf
```

### 7. Dry Run Testing

Test the updated workflow in dry-run mode:

```bash
# Trigger workflow with dry-run
# Via GitHub UI: Actions → Release → Run workflow → Select dry_run: true

# Or via GitHub CLI
gh workflow run release.yml -f version_type=patch -f dry_run=true
```

Monitor the workflow execution and verify:
- All dependencies install successfully
- No deprecation warnings appear
- All validation steps pass
- Build and test steps complete successfully

### 8. Commit and Document

Commit the changes with a descriptive message:

```bash
git add .github/workflow-dependencies.yml
git add docs/WORKFLOW_DEPENDENCIES.md
git add docs/DEPENDENCY_UPDATE_PROCEDURES.md
git add .github/workflows/release.yml

git commit -m "chore: update {package-name} to {new-version}

- Updated {package-name} from {old-version} to {new-version}
- Reason: {security fix / new features / bug fixes}
- Breaking changes: {none / list changes}
- Tested on Python 3.12 and 3.13
- All validation and tests pass

Refs: {issue-number or PR-number}"

git push origin main
```

## Upgrade Paths

### Security Updates (Critical)

**Priority**: Immediate
**Testing**: Expedited but thorough

```bash
# 1. Identify security vulnerability
safety check --json

# 2. Check for patched version
pip index versions {package-name}

# 3. Test patched version
python -m venv security_test
source security_test/bin/activate
pip install {package-name}=={patched-version}
pytest tests/
deactivate

# 4. Update immediately
# Follow steps 4-8 from Update Process

# 5. Verify fix
safety check
```

### Minor Version Updates

**Priority**: Regular maintenance
**Testing**: Standard

Minor version updates (e.g., 1.2.0 → 1.3.0) typically include:
- New features
- Bug fixes
- Performance improvements
- Backward compatibility maintained

```bash
# Follow full Update Process (steps 1-8)
# Pay special attention to:
# - New features that could benefit the workflow
# - Deprecation warnings for future major versions
# - Performance improvements
```

### Major Version Updates

**Priority**: Planned upgrade
**Testing**: Comprehensive

Major version updates (e.g., 1.x.x → 2.0.0) often include:
- Breaking changes
- API changes
- Removed deprecated features
- New architecture

```bash
# 1. Extensive pre-update assessment
# - Read full migration guide
# - Identify all breaking changes
# - Plan code modifications

# 2. Create feature branch
git checkout -b upgrade-{package-name}-v{major-version}

# 3. Update code for compatibility
# - Modify imports if needed
# - Update API calls
# - Remove deprecated feature usage

# 4. Comprehensive testing
# - Unit tests
# - Integration tests
# - End-to-end workflow tests

# 5. Update documentation
# - Document breaking changes
# - Update usage examples
# - Add migration notes

# 6. Create pull request
# - Detailed description of changes
# - Test results
# - Migration guide for users

# 7. Review and merge
# - Code review
# - Final testing
# - Merge to main
```

## Rollback Procedures

If a dependency update causes issues, follow these rollback procedures:

### Immediate Rollback (Production Issue)

```bash
# 1. Identify the problematic dependency
# Check workflow logs for errors

# 2. Revert to previous version in workflow files
git log --oneline -- .github/workflows/release.yml
git show {commit-hash}:.github/workflows/release.yml > .github/workflows/release.yml

# 3. Update documentation to reflect rollback
# Edit .github/workflow-dependencies.yml
# Add note about the issue

# 4. Commit rollback
git add .github/workflows/release.yml .github/workflow-dependencies.yml
git commit -m "revert: rollback {package-name} to {previous-version}

Issue: {description of problem}
Impact: {what failed}
Resolution: Rolled back to {previous-version}

Tracking issue: #{issue-number}"

git push origin main

# 5. Create issue to track resolution
gh issue create --title "Dependency update issue: {package-name} {new-version}" \
  --body "## Problem
{description}

## Impact
{what failed}

## Rollback
Rolled back to {previous-version}

## Next Steps
- [ ] Investigate root cause
- [ ] Test fix in isolation
- [ ] Retry update with fix"
```

### Planned Rollback (Testing Failure)

```bash
# 1. Document the issue
# Create detailed notes about what failed

# 2. Revert changes in feature branch
git checkout upgrade-{package-name}-v{version}
git revert {commit-hash}

# 3. Update documentation
# Add notes about the attempted update and issues

# 4. Close or update pull request
# Document findings and next steps

# 5. Create tracking issue
# Plan for future retry with fixes
```

### Partial Rollback (Specific Component)

If only specific functionality is affected:

```bash
# 1. Identify affected component
# Review error logs and test failures

# 2. Pin dependency version for specific use case
# In workflow file:
pip install {package-name}=={previous-version}  # Temporary pin due to issue #{number}

# 3. Document temporary pin
# Add comment in workflow file and documentation

# 4. Create issue for permanent fix
# Track work to resolve compatibility issue
```

## Dependency-Specific Procedures

### requests

**Update Frequency**: Quarterly or for security fixes
**Critical**: Yes (used for PyPI API interaction)

```bash
# Test checklist:
# - [ ] PyPI API calls work correctly
# - [ ] SSL certificate validation works
# - [ ] Timeout handling is correct
# - [ ] Error handling for network issues
```

### tomli-w

**Update Frequency**: Annually or for bug fixes
**Critical**: Yes (used for version updates)

```bash
# Test checklist:
# - [ ] TOML writing preserves structure
# - [ ] Version updates work correctly
# - [ ] No data loss or corruption
# - [ ] Compatible with tomllib (reading)
```

### build, twine, wheel, setuptools

**Update Frequency**: Before major releases
**Critical**: Yes (core build tools)

```bash
# Test checklist:
# - [ ] Package builds successfully
# - [ ] Wheel format is correct
# - [ ] Source distribution is complete
# - [ ] Twine validation passes
# - [ ] Upload to PyPI works (test with TestPyPI)
```

### bandit, safety

**Update Frequency**: Monthly (security tools)
**Critical**: Yes (security scanning)

```bash
# Test checklist:
# - [ ] Security scans complete successfully
# - [ ] No false positives introduced
# - [ ] Vulnerability database is current
# - [ ] Report format is compatible
```

## Monitoring and Maintenance

### Regular Checks

**Monthly**:
```bash
# Check for security updates
safety check --json
pip list --outdated | grep -E "(requests|tomli-w|bandit|safety|twine)"

# Review security advisories
# Visit GitHub Security Advisories for each package
```

**Quarterly**:
```bash
# Full dependency review
python scripts/validate_dependencies.py --verbose

# Check all packages for updates
pip list --outdated

# Review and plan updates
# Prioritize security fixes, then bug fixes, then features
```

**Annually**:
```bash
# Major version upgrade planning
# Review all dependencies for major version updates
# Plan migration for breaking changes
# Schedule upgrade windows
```

### Automated Monitoring

Consider setting up automated dependency monitoring:

```yaml
# .github/workflows/dependency-check.yml
name: Dependency Check
on:
  schedule:
    - cron: '0 0 * * 1'  # Weekly on Monday
  workflow_dispatch:

jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - name: Check for updates
        run: |
          pip install -e ".[dev]"
          pip list --outdated
          safety check
```

## Troubleshooting

### Update Fails to Install

**Symptoms**: `pip install` fails with dependency conflicts

**Resolution**:
```bash
# 1. Check dependency tree
pip install pipdeptree
pipdeptree -p {package-name}

# 2. Identify conflicts
pip install {package-name}=={new-version} --dry-run

# 3. Resolve conflicts
# Update conflicting dependencies first
# Or pin to compatible versions
```

### Tests Fail After Update

**Symptoms**: Tests pass before update, fail after

**Resolution**:
```bash
# 1. Identify failing tests
pytest tests/ -v --tb=short

# 2. Check for API changes
# Review package changelog for breaking changes

# 3. Update test code
# Modify tests to work with new API

# 4. Verify fix
pytest tests/ -v
```

### Workflow Fails in CI

**Symptoms**: Local tests pass, CI fails

**Resolution**:
```bash
# 1. Check CI environment
# Verify Python version matches
# Check for environment-specific issues

# 2. Reproduce locally
# Use same Python version as CI
# Test in clean environment

# 3. Update workflow
# Add missing dependencies
# Fix environment-specific issues
```

## Dependency Change Checklist

Use this checklist whenever making dependency-related changes to ensure consistency and prevent issues:

### Pre-Change Checklist

- [ ] **Verify package name on PyPI**
  ```bash
  pip index versions {package-name}
  # Or visit: https://pypi.org/project/{package-name}/
  ```

- [ ] **Check current dependency status**
  ```bash
  python scripts/validate_dependencies.py --verbose
  ```

- [ ] **Review package documentation**
  - Read package README and changelog
  - Check Python version compatibility
  - Review security advisories

- [ ] **Identify impact scope**
  - Which workflow steps use this dependency?
  - Are there any dependent packages?
  - What functionality relies on this package?

### Change Implementation Checklist

- [ ] **Update workflow file** (`.github/workflows/release.yml`)
  - Use correct package name (verify on PyPI)
  - Specify appropriate version constraint
  - Add inline comment explaining purpose if not obvious

- [ ] **Update dependency specification** (`.github/workflow-dependencies.yml`)
  - Update package name and version
  - Document reason for change
  - Add any relevant notes or warnings

- [ ] **Update documentation**
  - Update `docs/WORKFLOW_DEPENDENCIES.md` with new version
  - Add entry to changelog if significant
  - Update troubleshooting guides if needed

- [ ] **Run validation**
  ```bash
  python scripts/validate_dependencies.py --verbose --fail-on-warnings
  ```

### Testing Checklist

- [ ] **Test in isolation**
  ```bash
  python -m venv test_env
  source test_env/bin/activate
  pip install {package-name}=={version}
  # Test functionality
  deactivate
  rm -rf test_env
  ```

- [ ] **Validate TOML files** (if TOML-related change)
  ```bash
  python scripts/validate_toml.py pyproject.toml --type pyproject --verbose
  ```

- [ ] **Run workflow in dry-run mode**
  ```bash
  gh workflow run release.yml -f version_type=patch -f dry_run=true
  ```

- [ ] **Monitor workflow execution**
  - Check all steps complete successfully
  - Verify no deprecation warnings
  - Confirm expected behavior

### Post-Change Checklist

- [ ] **Commit with descriptive message**
  ```bash
  git add .github/workflows/release.yml .github/workflow-dependencies.yml docs/
  git commit -m "chore: update {package} dependency

  - Updated {package} from {old-version} to {new-version}
  - Reason: {security fix / bug fix / new feature}
  - Tested: {test summary}
  - Breaking changes: {none / list changes}"
  ```

- [ ] **Create pull request** (if using PR workflow)
  - Include test results
  - Document any breaking changes
  - Link to related issues

- [ ] **Monitor production workflow**
  - Watch first production run after merge
  - Verify successful completion
  - Check for any unexpected behavior

- [ ] **Document lessons learned**
  - Update troubleshooting guides if issues encountered
  - Add notes to dependency specification
  - Share knowledge with team

## Handling Future Dependency Issues

### Issue Detection

**Symptoms of dependency issues**:
- Workflow fails during dependency installation
- Package not found errors
- Version conflict errors
- Import errors during workflow execution
- Unexpected behavior after dependency update

**Detection methods**:
```bash
# Run validation script
python scripts/validate_dependencies.py --verbose

# Check workflow logs
gh run list --workflow=release.yml --limit 5

# Test locally
pip install -r requirements.txt  # or pip install -e ".[dev]"
```

### Issue Resolution Process

1. **Identify the problem**
   ```bash
   # Check validation output
   python scripts/validate_dependencies.py --verbose

   # Review workflow logs
   gh run view {run-id} --log-failed

   # Test package installation
   pip install {package-name}
   ```

2. **Determine root cause**
   - Incorrect package name? (e.g., `tomllib-w` vs `tomli-w`)
   - Version incompatibility?
   - Package removed from PyPI?
   - Network/PyPI outage?
   - Python version incompatibility?

3. **Implement fix**
   - Correct package name if wrong
   - Adjust version constraints if needed
   - Find alternative package if removed
   - Wait and retry if temporary outage

4. **Validate fix**
   ```bash
   # Validate dependencies
   python scripts/validate_dependencies.py --verbose

   # Test in isolation
   python -m venv test_fix
   source test_fix/bin/activate
   pip install {corrected-package}
   deactivate
   rm -rf test_fix

   # Run workflow in dry-run
   gh workflow run release.yml -f version_type=patch -f dry_run=true
   ```

5. **Document and prevent**
   - Update documentation with issue and resolution
   - Add validation checks if applicable
   - Update troubleshooting guides
   - Share knowledge with team

### Common Dependency Issues and Solutions

#### Issue: Package Name Error

**Example**: `tomllib-w` instead of `tomli-w`

**Solution**:
```bash
# 1. Verify correct name on PyPI
pip index versions tomli-w

# 2. Update workflow file
# Change: pip install tomllib-w
# To: pip install tomli-w

# 3. Validate fix
python scripts/validate_dependencies.py --verbose
```

**Prevention**: Always run validation script before committing

#### Issue: Version Conflict

**Example**: Package requires Python 3.13+ but workflow uses 3.12

**Solution**:
```bash
# 1. Check package requirements
pip index versions {package-name}
curl https://pypi.org/pypi/{package-name}/json | jq '.info.requires_python'

# 2. Either:
#    a) Update Python version in workflow
#    b) Pin to compatible package version
#    c) Find alternative package

# 3. Test with target Python version
python3.12 -m venv test_compat
source test_compat/bin/activate
pip install {package-name}
deactivate
```

**Prevention**: Check Python compatibility before adding dependencies

#### Issue: Package Removed from PyPI

**Example**: Package deprecated or removed

**Solution**:
```bash
# 1. Confirm package status
curl -I https://pypi.org/pypi/{package-name}/json

# 2. Find alternative:
#    - Check package documentation for recommended replacement
#    - Search PyPI for alternatives
#    - Consider built-in alternatives

# 3. Update to alternative package
# Follow full update process

# 4. Test thoroughly
pytest tests/ -v
```

**Prevention**: Monitor package health and maintenance status

#### Issue: Import Name Mismatch

**Example**: `pip install package-name` but `import package_name`

**Solution**:
```bash
# 1. Check correct import name
pip show {package-name} | grep Name
python -c "import {package_name}; print({package_name}.__name__)"

# 2. Update code to use correct import
# Note: Install name often uses hyphens, import uses underscores

# 3. Document in workflow-dependencies.yml
```

**Prevention**: Test imports after installing new packages

### Emergency Procedures

#### Critical Workflow Failure

If the release workflow fails in production:

1. **Immediate rollback**
   ```bash
   # Revert to last working commit
   git log --oneline -- .github/workflows/release.yml
   git revert {commit-hash}
   git push origin main
   ```

2. **Notify team**
   - Create incident issue
   - Document failure details
   - Communicate impact

3. **Investigate offline**
   - Test fix in isolation
   - Validate thoroughly
   - Document root cause

4. **Deploy fix**
   - Follow full change checklist
   - Test in dry-run mode first
   - Monitor closely

#### Security Vulnerability

If a dependency has a security vulnerability:

1. **Assess severity**
   ```bash
   safety check --json
   ```

2. **Check for patched version**
   ```bash
   pip index versions {package-name}
   ```

3. **Expedited update**
   - Follow update process but prioritize speed
   - Test critical functionality only
   - Deploy as soon as validated

4. **Verify fix**
   ```bash
   safety check
   ```

## Best Practices

1. **Always test in isolation first** - Never update dependencies directly in production
2. **Pin critical dependencies** - Use exact versions for stability-critical packages
3. **Document everything** - Record reasons for updates and any issues encountered
4. **Test thoroughly** - Run full test suite on all supported Python versions
5. **Update regularly** - Don't let dependencies get too far behind
6. **Monitor security** - Prioritize security updates over feature updates
7. **Have a rollback plan** - Always be prepared to revert if needed
8. **Communicate changes** - Document updates in changelog and release notes
9. **Use validation tools** - Run `validate_dependencies.py` before every commit
10. **Follow the checklist** - Use the dependency change checklist for consistency

## References

- [Python Packaging Guide](https://packaging.python.org/)
- [PyPI Package Index](https://pypi.org/)
- [Semantic Versioning](https://semver.org/)
- [Workflow Dependencies Documentation](./WORKFLOW_DEPENDENCIES.md)
- [Security Setup Guide](./SECURITY_SETUP.md)

## Changelog

### 2024-10-23
- Initial documentation created
- Comprehensive update procedures documented
- Rollback procedures established
- Dependency-specific guidelines added
