# Release Workflow Documentation

This document provides comprehensive guidance for using the automated release workflow in the Riveter project. The release workflow automates version management, testing, building, and publishing to both PyPI and GitHub releases.

## Table of Contents

- [Overview](#overview)
- [Triggering Releases](#triggering-releases)
- [Secret Setup and Configuration](#secret-setup-and-configuration)
- [Release Process Flow](#release-process-flow)
- [Troubleshooting Guide](#troubleshooting-guide)
- [Examples](#examples)
- [Security Considerations](#security-considerations)
- [Maintenance Procedures](#maintenance-procedures)

## Overview

The automated release workflow is implemented as a GitHub Actions workflow that:

- ✅ Validates prerequisites and permissions
- 🧪 Runs comprehensive tests across multiple platforms and Python versions
- 🔒 Performs security scans and quality checks
- 📦 Builds and validates packages
- 🚀 Publishes to PyPI (production releases)
- 🏷️ Creates GitHub releases with assets
- 📋 Updates changelog and version information

### Key Features

- **Manual Control**: Releases are triggered manually through GitHub UI
- **Semantic Versioning**: Supports patch, minor, and major version bumps
- **Dry Run Mode**: Test the workflow without publishing
- **Multi-Platform Testing**: Tests on Ubuntu, Windows, and macOS
- **Security First**: Comprehensive security validation and secret management
- **Rollback Support**: Automatic rollback documentation for failed releases

## Triggering Releases

### Prerequisites

Before triggering a release, ensure:

1. **Branch**: You are on the `main` branch
2. **Permissions**: You have write access to the repository
3. **Tests**: All existing tests are passing
4. **Changelog**: CHANGELOG.md has unreleased changes (if applicable)
5. **Secrets**: Required secrets are configured (see [Secret Setup](#secret-setup-and-configuration))

### Step-by-Step Release Process

#### 1. Navigate to GitHub Actions

1. Go to your repository on GitHub
2. Click on the **Actions** tab
3. Find the **Release** workflow in the left sidebar

#### 2. Trigger the Workflow

1. Click **Run workflow** button (top right)
2. Configure the release parameters:

   **Version Type** (required):
   - `patch`: Bug fixes and minor updates (1.0.0 → 1.0.1)
   - `minor`: New features, backward compatible (1.0.0 → 1.1.0)
   - `major`: Breaking changes (1.0.0 → 2.0.0)

   **Dry Run** (optional):
   - `false` (default): Full release with publishing
   - `true`: Test run without publishing to PyPI

3. Click **Run workflow**

#### 3. Monitor Progress

The workflow will show progress through these stages:

1. **Validate** - Prerequisites and permissions
2. **Test** - Multi-platform comprehensive testing
3. **Security-scan** - Security and quality checks
4. **Build-validation** - Package building and validation
5. **Version-management** - Version updates and tagging
6. **Changelog** - Changelog processing
7. **Build** - Final package building
8. **Publish-pypi** - PyPI publication (if not dry run)
9. **Github-release** - GitHub release creation
10. **Summary** - Final status report

### Release Parameters Explained

#### Version Type Selection Guide

| Version Type | When to Use | Example |
|--------------|-------------|---------|
| **patch** | Bug fixes, documentation updates, minor improvements | 1.2.3 → 1.2.4 |
| **minor** | New features, enhancements, backward-compatible changes | 1.2.3 → 1.3.0 |
| **major** | Breaking changes, major refactoring, API changes | 1.2.3 → 2.0.0 |

#### Dry Run Mode

Use dry run mode to:
- Test the release workflow without publishing
- Validate that all tests pass
- Check package building process
- Verify changelog processing
- Ensure secrets are properly configured

## Secret Setup and Configuration

### Required Secrets

The release workflow requires the following repository secrets:

#### 1. PYPI_API_TOKEN (Required for production releases)

**Purpose**: Authenticates with PyPI for package publishing

**Setup Instructions**:

1. **Generate PyPI API Token**:
   - Go to [PyPI Account Settings](https://pypi.org/manage/account/)
   - Navigate to "API tokens" section
   - Click "Add API token"
   - Set scope to "Entire account" or specific to "riveter" project
   - Copy the generated token (starts with `pypi-`)

2. **Add to GitHub Repository**:
   - Go to repository Settings → Secrets and variables → Actions
   - Click "New repository secret"
   - Name: `PYPI_API_TOKEN`
   - Value: Paste the PyPI token
   - Click "Add secret"

**Security Notes**:
- Token should start with `pypi-` and be 200+ characters
- Use project-scoped tokens when possible
- Rotate tokens every 90 days
- Never share or commit tokens to code

#### 2. GITHUB_TOKEN (Automatically provided)

**Purpose**: Repository operations (tags, releases)

**Setup**: No action required - GitHub automatically provides this token with appropriate permissions.

### Secret Validation

The workflow automatically validates secrets:

```yaml
# Example validation output
🔐 Secret Configuration Audit:
   PYPI_API_TOKEN: ✅ Configured
   GITHUB_TOKEN: ✅ Available
   Token format: ✅ Valid
   Token length: ✅ Sufficient
```

### Environment Configuration

For additional security, consider setting up environment protection rules:

1. Go to repository Settings → Environments
2. Create environment named `pypi`
3. Add protection rules:
   - Required reviewers
   - Wait timer
   - Deployment branches (main only)

## Release Process Flow

### Detailed Workflow Stages

#### Stage 1: Validation (2-3 minutes)
- Branch validation (must be `main`)
- User permission checks
- Current version extraction
- Secret availability verification
- Comprehensive pre-release validation

#### Stage 2: Testing (10-15 minutes)
- Multi-platform testing (Ubuntu, Windows, macOS)
- Multi-Python version testing (3.12, 3.13)
- Unit tests with coverage reporting
- Integration tests
- CLI functionality validation

#### Stage 3: Security & Quality (5-8 minutes)
- Security scanning with Bandit
- Dependency vulnerability checks with Safety
- Code quality checks (linting, formatting, type checking)
- Security configuration audit

#### Stage 4: Build Validation (3-5 minutes)
- Package building (wheel and source distribution)
- Package integrity validation
- Installation testing
- Artifact preparation

#### Stage 5: Version Management (1-2 minutes)
- Version calculation based on type
- pyproject.toml updates
- Git tag creation and pushing
- Tag uniqueness validation

#### Stage 6: Changelog Processing (1-2 minutes)
- CHANGELOG.md parsing and updates
- Release notes extraction
- Date formatting and insertion

#### Stage 7: Final Build (2-3 minutes)
- Clean package building
- Final validation checks
- Artifact upload preparation

#### Stage 8: PyPI Publication (2-5 minutes, production only)
- PyPI authentication validation
- Package upload with retry logic
- Publication verification
- URL generation

#### Stage 9: GitHub Release (2-3 minutes)
- Release creation with assets
- Release description formatting
- Asset upload verification
- Release URL generation

#### Stage 10: Summary (1 minute)
- Final status compilation
- Success/failure reporting
- Asset and URL summary

### Total Time Estimate
- **Dry Run**: 25-35 minutes
- **Production Release**: 30-45 minutes

## Troubleshooting Guide

### Common Issues and Solutions

#### 1. "Releases can only be triggered from the main branch"

**Problem**: Workflow triggered from wrong branch

**Solution**:
```bash
# Switch to main branch
git checkout main
git pull origin main

# Then trigger workflow from GitHub UI
```

#### 2. "PYPI_API_TOKEN secret not found"

**Problem**: PyPI token not configured or incorrectly named

**Solutions**:
- Verify secret name is exactly `PYPI_API_TOKEN`
- Check secret is added to repository (not environment)
- Regenerate token if expired
- Use dry run mode to test without PyPI token

#### 3. "Tag v1.2.3 already exists"

**Problem**: Version tag already exists in repository

**Solutions**:
```bash
# Check existing tags
git tag -l

# Delete tag locally and remotely (if needed)
git tag -d v1.2.3
git push origin :refs/tags/v1.2.3

# Or choose different version type
```

#### 4. "Package build failed"

**Problem**: Issues with package configuration or dependencies

**Solutions**:
- Check pyproject.toml syntax
- Verify all dependencies are properly specified
- Test build locally:
```bash
python -m build
twine check dist/*
```

#### 5. "PyPI publication failed"

**Problem**: Authentication or package issues

**Solutions**:
- Verify PyPI token permissions
- Check if package version already exists on PyPI
- Ensure package name matches PyPI project
- Review PyPI upload logs for specific errors

#### 6. "Tests failed on platform X"

**Problem**: Platform-specific test failures

**Solutions**:
- Review test logs for specific platform
- Check for platform-specific dependencies
- Verify file path handling (Windows vs Unix)
- Test locally on failing platform if possible

#### 7. "Security scan failed"

**Problem**: Security vulnerabilities detected

**Solutions**:
- Review Bandit security scan results
- Update vulnerable dependencies
- Add security exceptions if false positives
- Check Safety vulnerability report

#### 8. "GitHub release creation failed"

**Problem**: GitHub API or permission issues

**Solutions**:
- Verify GITHUB_TOKEN permissions
- Check repository access settings
- Ensure tag was created successfully
- Review GitHub API rate limits

### Debugging Steps

#### 1. Check Workflow Logs
1. Go to Actions tab → Failed workflow run
2. Click on failed job
3. Expand failed step
4. Review error messages and stack traces

#### 2. Validate Prerequisites Locally
```bash
# Check current version
grep -E '^version = ' pyproject.toml

# Verify tests pass
pytest tests/ -v

# Test package building
python -m build
twine check dist/*

# Check security
bandit -r src/
safety check
```

#### 3. Test with Dry Run
Always test with dry run first:
1. Set "Dry Run" to `true`
2. Monitor all stages except PyPI publication
3. Verify all validations pass
4. Then run production release

#### 4. Review Security Configuration
```bash
# Check repository secrets (via GitHub UI)
# Settings → Secrets and variables → Actions

# Verify token format
# PyPI token should start with 'pypi-'
# Should be 200+ characters long
```

### Getting Help

If issues persist:

1. **Check Documentation**:
   - [SECURITY_SETUP.md](SECURITY_SETUP.md) - Security configuration
   - [TECHNICAL.md](TECHNICAL.md) - Technical details
   - [CONTRIBUTING.md](../CONTRIBUTING.md) - Development setup

2. **Create Issue**:
   - Include workflow run URL
   - Copy relevant error messages
   - Specify environment details
   - Mention troubleshooting steps tried

3. **Emergency Rollback**:
   - Failed releases automatically generate rollback documentation
   - Check workflow artifacts for rollback instructions
   - Manual rollback may be required for partial failures

## Examples

### Example 1: Patch Release (Bug Fix)

**Scenario**: Fixing a bug in the rule validation logic

**Steps**:
1. Merge bug fix to `main` branch
2. Go to Actions → Release workflow
3. Click "Run workflow"
4. Select:
   - Version type: `patch`
   - Dry run: `false`
5. Click "Run workflow"

**Expected Outcome**:
- Version: 1.2.3 → 1.2.4
- PyPI: https://pypi.org/project/riveter/1.2.4/
- GitHub: Release v1.2.4 with assets

**Workflow Output Example**:
```
🚀 Release Summary
Version: 1.2.4
Tag: v1.2.4
Dry Run: false

Pre-Release Testing Results:
- ✅ Validation: success
- 🧪 Comprehensive Tests: success
  - Test Results: Validation:success,Tests:success,Security:success,Build:success
  - Overall Status: passed

Release Pipeline Status:
- ✅ Version Management: success
- ✅ Changelog: success
- ✅ Build: success
- 📦 PyPI Publish: success
- 🏷️ GitHub Release: success

🎉 Release completed successfully!
📦 PyPI: https://pypi.org/project/riveter/1.2.4/
🏷️ GitHub: https://github.com/riveter/riveter/releases/tag/v1.2.4
```

### Example 2: Minor Release (New Feature)

**Scenario**: Adding new rule pack for GCP security

**Steps**:
1. Merge feature branch to `main`
2. Update CHANGELOG.md with new features
3. Trigger release workflow:
   - Version type: `minor`
   - Dry run: `false`

**Expected Outcome**:
- Version: 1.2.4 → 1.3.0
- New features documented in release notes
- Updated changelog with release date

### Example 3: Dry Run Testing

**Scenario**: Testing release process before production

**Steps**:
1. Trigger workflow with:
   - Version type: `patch`
   - Dry run: `true`
2. Monitor all stages
3. Verify no publishing occurs

**Expected Outcome**:
```
ℹ️ This was a dry run - no actual publishing occurred
✅ All pre-release tests passed - release would proceed in production mode

GitHub Release (Dry Run)
Tag: v1.2.5
Title: Release 1.2.5
Assets: riveter-1.2.5-py3-none-any.whl, riveter-1.2.5.tar.gz

ℹ️ Release would be created with the above configuration
```

### Example 4: Major Release (Breaking Changes)

**Scenario**: Major API refactoring with breaking changes

**Steps**:
1. Ensure comprehensive testing of breaking changes
2. Update documentation for API changes
3. Trigger release:
   - Version type: `major`
   - Dry run: `false` (after successful dry run)

**Expected Outcome**:
- Version: 1.3.0 → 2.0.0
- Major version bump indicates breaking changes
- Comprehensive release notes with migration guide

### Example 5: Failed Release Recovery

**Scenario**: Release fails during PyPI publication

**Workflow Output**:
```
❌ PyPI publication failed after 5 attempts
📖 Troubleshooting guide: docs/SECURITY_SETUP.md
🔄 Rollback documentation created
```

**Recovery Steps**:
1. Check rollback documentation in workflow artifacts
2. Verify PyPI token permissions
3. Delete created git tag if needed:
   ```bash
   git tag -d v1.2.5
   git push origin :refs/tags/v1.2.5
   ```
4. Fix underlying issue
5. Re-trigger release workflow

## Security Considerations

### Token Security

**Best Practices**:
- Use project-scoped PyPI tokens when possible
- Rotate tokens every 90 days
- Monitor token usage in PyPI account settings
- Never commit tokens to code or logs

**Token Validation**:
The workflow validates:
- Token format (starts with `pypi-`)
- Token length (200+ characters)
- Token scope and permissions
- Token expiration (if detectable)

### Workflow Security

**Access Control**:
- Only repository maintainers can trigger releases
- Releases restricted to `main` branch only
- Manual approval required (no automatic triggers)
- Comprehensive audit logging

**Environment Security**:
- Minimal required permissions
- Secure credential handling
- No credential exposure in logs
- Network isolation in GitHub Actions

### Supply Chain Security

**Package Integrity**:
- Comprehensive testing before release
- Security scanning with Bandit and Safety
- Package validation with twine check
- Checksum verification for dependencies

**Release Verification**:
- Multi-stage validation process
- Publication verification on PyPI
- Asset integrity checks
- Automated rollback documentation

## Maintenance Procedures

### Regular Maintenance Tasks

#### Monthly Tasks
- [ ] Review and rotate PyPI API tokens (every 90 days)
- [ ] Check for workflow dependency updates
- [ ] Review security scan results and trends
- [ ] Validate backup and recovery procedures

#### Quarterly Tasks
- [ ] Audit repository access permissions
- [ ] Review and update security policies
- [ ] Test complete release workflow end-to-end
- [ ] Update documentation for any process changes

#### Annual Tasks
- [ ] Comprehensive security audit
- [ ] Review and update emergency procedures
- [ ] Validate disaster recovery processes
- [ ] Update security training materials

### Token Rotation Procedure

**PyPI Token Rotation**:
1. Generate new PyPI API token
2. Test token with dry run release
3. Update GitHub repository secret
4. Revoke old token from PyPI
5. Document rotation in security log

**Validation Steps**:
```bash
# Test new token (dry run)
# 1. Update secret in GitHub
# 2. Trigger dry run release
# 3. Verify authentication succeeds
# 4. Revoke old token only after success
```

### Workflow Updates

**Dependency Updates**:
- Monitor GitHub Actions marketplace for updates
- Test updates in fork before applying to main
- Update pinned versions in workflow file
- Validate security implications of updates

**Security Updates**:
- Subscribe to GitHub Security Advisories
- Monitor Python security announcements
- Update security scanning tools regularly
- Review and update security policies

### Monitoring and Alerting

**Key Metrics to Monitor**:
- Release success/failure rates
- Average release duration
- Security scan results trends
- Token usage and expiration dates

**Alerting Setup**:
- Failed release notifications
- Security scan failures
- Token expiration warnings
- Unusual access patterns

### Emergency Procedures

**Release Rollback**:
1. Identify failed release version
2. Check rollback documentation (auto-generated)
3. Delete problematic release from GitHub
4. Remove package from PyPI (if possible)
5. Revert version changes in repository
6. Communicate rollback to users

**Security Incident Response**:
1. Immediately rotate all tokens
2. Review access logs for unauthorized activity
3. Audit recent releases for compromise
4. Update security measures
5. Document incident and lessons learned

### Documentation Maintenance

**Keep Updated**:
- Release workflow documentation
- Security setup procedures
- Troubleshooting guides
- Example workflows and outputs

**Review Schedule**:
- After each major workflow change
- Following security incidents
- Quarterly documentation review
- Annual comprehensive update

---

## Additional Resources

- **[SECURITY_SETUP.md](SECURITY_SETUP.md)** - Detailed security configuration
- **[TECHNICAL.md](TECHNICAL.md)** - Technical implementation details
- **[CONTRIBUTING.md](../CONTRIBUTING.md)** - Development and contribution guidelines
- **[GitHub Actions Documentation](https://docs.github.com/en/actions)** - Official GitHub Actions docs
- **[PyPI Help](https://pypi.org/help/)** - PyPI documentation and support

---

*This documentation is maintained as part of the automated release workflow. For questions or improvements, please create an issue or submit a pull request.*
