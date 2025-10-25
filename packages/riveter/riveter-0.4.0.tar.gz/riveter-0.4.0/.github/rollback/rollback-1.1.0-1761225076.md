# Release Rollback Guide - 1.1.0

## Overview
This document provides instructions for rolling back a failed release of version 1.1.0.

## Rollback Steps

### 1. Remove Git Tag (if created)
```bash
# Remove local tag
git tag -d v1.1.0

# Remove remote tag (if pushed)
git push origin --delete v1.1.0
```

### 2. Revert Version Changes
```bash
# Reset pyproject.toml to previous version
git checkout HEAD~1 -- pyproject.toml

# Or manually edit pyproject.toml to restore previous version
```

### 3. Revert Changelog Changes
```bash
# Reset CHANGELOG.md to previous state
git checkout HEAD~1 -- CHANGELOG.md

# Or manually restore the [Unreleased] section
```

### 4. Clean Up Build Artifacts
```bash
# Remove build artifacts
rm -rf dist/ build/ *.egg-info/

# Clean up any temporary files
git clean -fd
```

### 5. PyPI Cleanup (if package was published)
⚠️ **Note**: PyPI does not allow deleting published packages. If the package was successfully published to PyPI, you cannot remove it. Instead:

- Publish a new patch version with fixes
- Mark the problematic version as yanked (if critical issues exist)
- Update documentation to note the issue

### 6. GitHub Release Cleanup (if created)
```bash
# Delete the GitHub release via API or web interface
# The release can be deleted from: https://github.com/owner/repo/releases
```

### 7. Verify Rollback
```bash
# Check current version
grep version pyproject.toml

# Check git tags
git tag -l | grep 1.1.0

# Check git status
git status
```

## Prevention for Next Release

1. **Run dry-run first**: Always test with `dry_run: true`
2. **Check all validations**: Ensure all pre-release checks pass
3. **Review changes**: Manually review version and changelog updates
4. **Test locally**: Build and test packages locally before release

## Emergency Contacts

- Repository maintainers: Check CODEOWNERS file
- GitHub repository: https://github.com/owner/repo
- Issues: https://github.com/owner/repo/issues

---
Generated on: 2025-10-23 09:11:16 UTC
Workflow run: unknown
