# Release Workflow Quick Reference

Quick reference guide for maintainers to trigger releases efficiently.

## 🚀 Quick Release Steps

### 1. Pre-Release Checklist
- [ ] On `main` branch with latest changes
- [ ] All tests passing locally
- [ ] CHANGELOG.md updated (if applicable)
- [ ] PyPI token configured (for production releases)

### 2. Trigger Release
1. **GitHub Actions** → **Release** workflow
2. **Run workflow** → Configure:
   - **Version type**: `patch` | `minor` | `major`
   - **Dry run**: `true` (test) | `false` (production)
3. **Run workflow**

### 3. Monitor Progress
Watch for these stages (30-45 min total):
- ✅ Validate → 🧪 Test → 🔒 Security → 📦 Build → 🚀 Publish → 🏷️ Release

## 📋 Version Type Guide

| Type | Use Case | Example |
|------|----------|---------|
| `patch` | Bug fixes, docs | 1.2.3 → 1.2.4 |
| `minor` | New features | 1.2.3 → 1.3.0 |
| `major` | Breaking changes | 1.2.3 → 2.0.0 |

## 🔧 Common Issues

| Issue | Quick Fix |
|-------|-----------|
| Wrong branch | Switch to `main` branch |
| Missing PyPI token | Add `PYPI_API_TOKEN` secret |
| Tag exists | Delete tag: `git tag -d v1.2.3` |
| Tests fail | Fix tests, then re-trigger |

## 🔐 Required Secrets

- **PYPI_API_TOKEN**: PyPI publishing (production only)
- **GITHUB_TOKEN**: Auto-provided by GitHub

## 📖 Full Documentation

For detailed information, see [RELEASE_WORKFLOW.md](RELEASE_WORKFLOW.md)

---

*Need help? Check the [troubleshooting guide](RELEASE_WORKFLOW.md#troubleshooting-guide) or create an issue.*
