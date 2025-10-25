# Security Setup for Automated Release Workflow

This document provides comprehensive instructions for setting up secure credentials and managing secrets for the automated release workflow.

## Required Repository Secrets

The automated release workflow requires the following secrets to be configured in your GitHub repository:

### 1. PYPI_API_TOKEN (Required for PyPI Publishing)

**Purpose**: Authenticates package uploads to PyPI
**Scope**: Upload packages to the `riveter` project only
**Format**: `pypi-AgEIcHlwaS5vcmc...` (starts with `pypi-`)

#### Setup Instructions:

1. **Generate PyPI API Token**:
   - Log in to [PyPI](https://pypi.org)
   - Go to Account Settings → API tokens
   - Click "Add API token"
   - Set token name: `riveter-github-actions`
   - Set scope: "Scope to project" → Select `riveter`
   - Copy the generated token (starts with `pypi-`)

2. **Add to GitHub Repository**:
   - Go to your repository on GitHub
   - Navigate to Settings → Secrets and variables → Actions
   - Click "New repository secret"
   - Name: `PYPI_API_TOKEN`
   - Value: Paste the PyPI token
   - Click "Add secret"

3. **Verify Token Format**:
   - Token must start with `pypi-`
   - Token should be project-scoped (not account-wide)
   - Test token validity before adding to repository

### 2. GITHUB_TOKEN (Automatically Provided)

**Purpose**: Authenticates GitHub API operations (releases, tags, repository access)
**Scope**: Automatically provided by GitHub Actions with repository permissions
**Format**: `ghp_...` or `ghs_...`

#### Configuration:

The `GITHUB_TOKEN` is automatically provided by GitHub Actions and doesn't require manual setup. However, ensure your workflow has the correct permissions:

```yaml
permissions:
  contents: write      # Required for creating tags and releases
  id-token: write     # Required for OIDC authentication
  actions: read       # Required for workflow execution
```

## Secret Validation

The workflow includes comprehensive secret validation to ensure security and prevent failures:

### Pre-Release Validation

1. **Secret Availability Check**:
   - Validates `PYPI_API_TOKEN` is present (non-dry-run mode only)
   - Confirms `GITHUB_TOKEN` is available
   - Fails early if required secrets are missing

2. **Token Format Validation**:
   - Verifies PyPI token starts with `pypi-`
   - Warns if token format appears incorrect
   - Validates token is not empty or malformed

3. **Permission Validation**:
   - Confirms workflow has required GitHub permissions
   - Validates user triggering release has appropriate access
   - Ensures release is triggered from main branch only

### Runtime Security Checks

1. **Credential Exposure Prevention**:
   - Secrets are never logged or exposed in outputs
   - Sensitive operations use secure parameter passing
   - Error messages don't include credential information

2. **Minimal Permission Usage**:
   - Each operation uses only required permissions
   - Tokens are scoped to specific operations
   - No unnecessary credential access

## Security Best Practices

### Token Management

1. **Regular Rotation**:
   - Rotate PyPI tokens every 90 days
   - Update repository secrets immediately after rotation
   - Test new tokens before removing old ones

2. **Scope Limitation**:
   - Use project-scoped PyPI tokens (not account-wide)
   - Limit GitHub token permissions to minimum required
   - Avoid using personal access tokens

3. **Access Control**:
   - Limit repository secret access to maintainers only
   - Use branch protection rules to control release triggers
   - Monitor secret usage through audit logs

### Workflow Security

1. **Branch Restrictions**:
   - Releases only allowed from `main` branch
   - Branch protection rules prevent unauthorized changes
   - Required status checks before merging

2. **User Permissions**:
   - Only repository maintainers can trigger releases
   - Workflow validates user permissions before proceeding
   - Failed permission checks abort the release process

3. **Audit Trail**:
   - All release actions logged in GitHub Actions
   - Secret usage tracked (without exposing values)
   - Failed attempts recorded for security monitoring

## Troubleshooting

### Common Issues

1. **"PYPI_API_TOKEN secret is required for publishing"**:
   - Ensure secret is added to repository settings
   - Verify secret name is exactly `PYPI_API_TOKEN`
   - Check token is not expired or revoked

2. **"PyPI token may not be in expected format"**:
   - Verify token starts with `pypi-`
   - Ensure complete token was copied (no truncation)
   - Generate new token if format is incorrect

3. **"Permission denied" errors**:
   - Check workflow permissions in YAML file
   - Verify user has maintainer access to repository
   - Ensure release is triggered from main branch

4. **"Package upload failed"**:
   - Verify PyPI token has upload permissions for project
   - Check if package version already exists on PyPI
   - Ensure token scope includes the correct project

### Secret Rotation Process

1. **Generate New Token**:
   - Create new PyPI API token with same scope
   - Test new token with a dry-run release
   - Keep old token active during transition

2. **Update Repository Secret**:
   - Replace `PYPI_API_TOKEN` value in repository settings
   - Verify new secret is saved correctly
   - Test workflow with new token

3. **Revoke Old Token**:
   - Only revoke old token after confirming new one works
   - Monitor for any failed workflows using old token
   - Update documentation with rotation date

### Security Incident Response

1. **Compromised Token**:
   - Immediately revoke token on PyPI
   - Remove secret from repository settings
   - Generate new token with different scope if needed
   - Review recent package uploads for unauthorized changes

2. **Unauthorized Release**:
   - Check GitHub Actions logs for release details
   - Verify user permissions and access logs
   - Consider revoking and regenerating all tokens
   - Review branch protection and access controls

## Monitoring and Maintenance

### Regular Security Checks

1. **Monthly Reviews**:
   - Review active PyPI tokens and their usage
   - Check GitHub Actions logs for unusual activity
   - Verify repository secret access permissions

2. **Quarterly Audits**:
   - Rotate PyPI API tokens
   - Review and update workflow permissions
   - Test security controls with dry-run releases

3. **Annual Security Assessment**:
   - Review entire release workflow security
   - Update security documentation
   - Assess new security features and best practices

### Compliance Considerations

1. **Access Logging**:
   - GitHub Actions provides comprehensive audit logs
   - PyPI tracks package upload history
   - Repository settings changes are logged

2. **Secret Storage**:
   - GitHub encrypts repository secrets at rest
   - Secrets are only accessible during workflow execution
   - No secret values are stored in workflow logs

3. **Network Security**:
   - All API communications use HTTPS/TLS
   - Token transmission is encrypted
   - No credentials transmitted over insecure channels

## Contact and Support

For security-related questions or incidents:

1. **Repository Issues**: Create a private security advisory
2. **PyPI Issues**: Contact PyPI support directly
3. **GitHub Actions**: Use GitHub Support channels
4. **Emergency**: Follow your organization's security incident response procedures

---

**Last Updated**: $(date +"%Y-%m-%d")
**Review Schedule**: Quarterly
**Next Review**: $(date -d "+3 months" +"%Y-%m-%d")
