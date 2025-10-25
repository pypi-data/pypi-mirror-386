# Dependency Management Quick Reference

Quick reference guide for common dependency management tasks.

## Quick Commands

### Check All Dependencies
```bash
python scripts/validate_dependencies.py --verbose
```

### Check for Updates
```bash
# Check single package
python scripts/update_dependency.py requests --check-only

# Check all installed packages
pip list --outdated
```

### Update a Dependency
```bash
# Test update (recommended)
python scripts/update_dependency.py requests --verbose

# Test specific version
python scripts/update_dependency.py requests --test-version 2.33.0 --verbose

# Dry run (see what would happen)
python scripts/update_dependency.py requests --dry-run
```

### Security Checks
```bash
# Check for vulnerabilities
safety check

# Security scan
bandit -r src/ -f txt
```

### Verify Package Name
```bash
# Check if package exists on PyPI
pip index versions {package-name}

# Or use curl
curl -s https://pypi.org/pypi/{package-name}/json | jq '.info.name'

# Common mistake: tomllib-w (wrong) vs tomli-w (correct)
pip index versions tomli-w  # ✅ Correct
pip index versions tomllib-w  # ❌ Does not exist
```

## Quick Checklists

### Adding New Dependency
- [ ] Verify package name on PyPI: `pip index versions {package}`
- [ ] Check Python compatibility
- [ ] Update `.github/workflows/release.yml`
- [ ] Update `.github/workflow-dependencies.yml`
- [ ] Update `docs/WORKFLOW_DEPENDENCIES.md`
- [ ] Run validation: `python scripts/validate_dependencies.py --verbose`
- [ ] Test in dry-run: `gh workflow run release.yml -f dry_run=true`
- [ ] Commit with descriptive message

### Fixing Dependency Issue
- [ ] Identify problem: `python scripts/validate_dependencies.py --verbose`
- [ ] Verify correct package name on PyPI
- [ ] Update workflow file with correct name/version
- [ ] Update documentation
- [ ] Validate fix: `python scripts/validate_dependencies.py --verbose`
- [ ] Test in dry-run mode
- [ ] Commit and monitor

### Before Committing Workflow Changes
- [ ] Run: `python scripts/validate_dependencies.py --verbose --fail-on-warnings`
- [ ] Run: `python scripts/validate_toml.py pyproject.toml --type pyproject --verbose`
- [ ] Review changes: `git diff .github/workflows/`
- [ ] Test locally if possible
- [ ] Commit with clear message

## Common Workflows

### Monthly Security Check
```bash
# 1. Check for vulnerabilities
safety check --json

# 2. Check for security updates
pip list --outdated | grep -E "(requests|tomli-w|bandit|safety|twine)"

# 3. Update if needed
python scripts/update_dependency.py {package} --verbose
```

### Quarterly Dependency Review
```bash
# 1. Validate all dependencies
python scripts/validate_dependencies.py --verbose

# 2. Check for updates
pip list --outdated

# 3. Review and plan updates
# See docs/DEPENDENCY_UPDATE_PROCEDURES.md
```

### Update Workflow
```bash
# 1. Check for updates
python scripts/update_dependency.py {package} --check-only

# 2. Review release notes
# Visit: https://pypi.org/project/{package}/

# 3. Test update
python scripts/update_dependency.py {package} --verbose

# 4. Update documentation
# Edit: .github/workflow-dependencies.yml
# Edit: docs/WORKFLOW_DEPENDENCIES.md

# 5. Test workflow
gh workflow run release.yml -f version_type=patch -f dry_run=true

# 6. Commit changes
git add .github/workflow-dependencies.yml docs/WORKFLOW_DEPENDENCIES.md
git commit -m "chore: update {package} to {version}"
```

### Rollback Workflow
```bash
# 1. Revert workflow file
git log --oneline -- .github/workflows/release.yml
git show {commit}:.github/workflows/release.yml > .github/workflows/release.yml

# 2. Update documentation
# Add note about rollback in .github/workflow-dependencies.yml

# 3. Commit rollback
git add .github/workflows/release.yml .github/workflow-dependencies.yml
git commit -m "revert: rollback {package} to {version}"

# 4. Create tracking issue
gh issue create --title "Dependency rollback: {package}"
```

## File Locations

### Configuration Files
- **Dependency Specification**: `.github/workflow-dependencies.yml`
- **Workflow File**: `.github/workflows/release.yml`

### Documentation
- **Main Documentation**: `docs/WORKFLOW_DEPENDENCIES.md`
- **Update Procedures**: `docs/DEPENDENCY_UPDATE_PROCEDURES.md`
- **This Quick Reference**: `docs/DEPENDENCY_QUICK_REFERENCE.md`

### Scripts
- **Validation Script**: `scripts/validate_dependencies.py`
- **Update Helper**: `scripts/update_dependency.py`
- **TOML Validation**: `scripts/validate_toml.py`

## Dependency Categories

### Validation Dependencies
- **requests**: HTTP requests for API validation
- **tomli-w**: Writing TOML files

### Build Dependencies
- **build**: Building Python packages
- **twine**: Uploading to PyPI
- **wheel**: Building wheel distributions
- **setuptools**: Package utilities

### Security Dependencies
- **bandit**: Security vulnerability scanning
- **safety**: Dependency vulnerability checking

## Version Pinning Strategy

### Critical Dependencies (Pin Exact Version)
```yaml
pip install requests==2.32.5
```
Use for: Production-critical packages

### Flexible Dependencies (Minimum Version)
```yaml
pip install tomli-w>=1.0.0
```
Use for: Most dependencies

### Latest Dependencies (No Pin)
```yaml
pip install safety
```
Use for: Security tools that need frequent updates

## Common Mistakes and How to Avoid Them

### Mistake 1: Wrong Package Name
**Example**: Using `tomllib-w` instead of `tomli-w`

**How to avoid**:
```bash
# Always verify on PyPI first
pip index versions tomli-w  # ✅ Exists
pip index versions tomllib-w  # ❌ Does not exist

# Use validation script
python scripts/validate_dependencies.py --verbose
```

### Mistake 2: Confusing Built-in and Third-Party
**Example**: Trying to install `tomllib` (built-in) from PyPI

**How to avoid**:
- Built-in (no install): `tomllib`, `json`, `pathlib`, `sys`
- Third-party (install): `tomli-w`, `requests`, `twine`
- Check Python docs for built-in modules

### Mistake 3: Import vs Install Name
**Example**: `pip install package-name` but `import package_name`

**How to avoid**:
```bash
# Install uses hyphens
pip install tomli-w

# Import uses underscores
python -c "import tomli_w"
```

### Mistake 4: Not Testing Before Commit
**How to avoid**:
```bash
# Always run before committing
python scripts/validate_dependencies.py --verbose --fail-on-warnings
```

### Mistake 5: Skipping Documentation Updates
**How to avoid**:
- Update `.github/workflow-dependencies.yml`
- Update `docs/WORKFLOW_DEPENDENCIES.md`
- Add notes about why the change was made

## Troubleshooting

### Package Not Found
```bash
# Verify package name
python scripts/validate_dependencies.py --verbose

# Check PyPI
curl https://pypi.org/pypi/{package}/json

# Common issue: tomllib-w vs tomli-w
# Correct: tomli-w (with hyphen)
```

### Installation Fails
```bash
# Check Python version compatibility
python scripts/update_dependency.py {package} --check-only

# Test in isolation
python scripts/update_dependency.py {package} --verbose
```

### Tests Fail After Update
```bash
# Run full test suite
pytest tests/ -v

# Check for breaking changes
# Review package changelog

# Rollback if needed
git revert {commit}
```

### Workflow Fails After Dependency Change
```bash
# Check workflow logs
gh run list --workflow=release.yml --limit 5
gh run view {run-id} --log-failed

# Validate dependencies
python scripts/validate_dependencies.py --verbose

# Test in dry-run
gh workflow run release.yml -f version_type=patch -f dry_run=true

# Rollback if needed
git revert {commit}
git push origin main
```

## Getting Help

- **Detailed Procedures**: See `docs/DEPENDENCY_UPDATE_PROCEDURES.md`
- **Full Documentation**: See `docs/WORKFLOW_DEPENDENCIES.md`
- **Security Setup**: See `docs/SECURITY_SETUP.md`

## Update Schedule

- **Monthly**: Security updates
- **Quarterly**: Dependency review
- **Annually**: Major version upgrades

## Best Practices

1. ✅ Always test in isolation first
2. ✅ Pin critical dependencies
3. ✅ Document all changes
4. ✅ Test thoroughly
5. ✅ Have a rollback plan
6. ✅ Monitor security
7. ✅ Update regularly
8. ✅ Review release notes

## Emergency Procedures

### Critical Security Vulnerability
```bash
# 1. Identify vulnerability
safety check --json

# 2. Test patched version immediately
python scripts/update_dependency.py {package} --test-version {patched} --verbose

# 3. Update and deploy
# Follow expedited update process

# 4. Verify fix
safety check
```

### Workflow Failure
```bash
# 1. Check workflow logs
gh run list --workflow=release.yml

# 2. Identify failing dependency
# Review error messages

# 3. Rollback immediately
git revert {commit}
git push origin main

# 4. Create tracking issue
gh issue create --title "Workflow failure: {description}"
```

---

**Last Updated**: 2024-10-23
**Version**: 1.0
