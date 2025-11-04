# PyPI Publishing Guide

## Overview

Kagura AI uses **Trusted Publisher (OIDC)** for secure, automated PyPI publishing via GitHub Actions.

## One-Time Setup

### 1. Configure PyPI Trusted Publisher

**For production releases (PyPI):**

1. Go to https://pypi.org/manage/account/publishing/
2. Click **"Add a new publisher"**
3. Fill in:
   - **Owner**: `JFK`
   - **Repository name**: `kagura-ai`
   - **Workflow name**: `deploy_pypi.yml`
   - **Environment name**: `pypi`
4. Click **"Add"**

**For testing (TestPyPI) - Optional:**

1. Go to https://test.pypi.org/manage/account/publishing/
2. Same settings as above (environment: `testpypi`)

### 2. Configure GitHub Environment (if not using Trusted Publisher)

If you prefer to use API tokens instead of Trusted Publisher:

1. Go to GitHub repository → Settings → Environments
2. Create environment: `pypi`
3. Add secret: `PYPI_API_TOKEN` (from PyPI account settings)
4. Create environment: `testpypi` (optional)
5. Add secret: `TEST_PYPI_API_TOKEN`

## Publishing Workflow

### Method 1: GitHub Release (Recommended)

```bash
# 1. Update version in pyproject.toml
vim pyproject.toml  # version = "4.0.12"

# 2. Update CHANGELOG.md
vim CHANGELOG.md

# 3. Commit and push
git add pyproject.toml CHANGELOG.md
git commit -m "chore(release): Release v4.0.12"
git push origin main

# 4. Create git tag
git tag v4.0.12
git push origin v4.0.12

# 5. Create GitHub Release
gh release create v4.0.12 \
  --title "v4.0.12 - Intel Mac Support & Python 3.13" \
  --notes-file CHANGELOG.md \
  --verify-tag

# 6. Workflow automatically:
#    - Runs all tests
#    - Builds distribution
#    - Publishes to PyPI (if full release)
#    - Publishes to TestPyPI (if prerelease)
#    - Uploads .whl and .tar.gz to GitHub Release
```

### Method 2: Manual Workflow Dispatch

For testing without creating a release:

```bash
# Via GitHub UI:
# Actions → Publish to PyPI → Run workflow → Select target (testpypi/pypi)

# Or via CLI:
gh workflow run deploy_pypi.yml -f publish_target=testpypi
```

## Prerelease vs Full Release

### Prerelease (→ TestPyPI)
```bash
gh release create v4.0.12-beta \
  --title "v4.0.12 Beta" \
  --notes "Beta release for testing" \
  --prerelease  # ← This sends to TestPyPI
```

### Full Release (→ PyPI)
```bash
gh release create v4.0.12 \
  --title "v4.0.12" \
  --notes-file CHANGELOG.md
  # No --prerelease flag → Goes to PyPI
```

## Workflow Features

### ✅ Modern Best Practices
- **Trusted Publisher (OIDC)**: No long-lived tokens, more secure
- **uv**: Fast builds (~2x faster than pip)
- **Official PyPA action**: pypa/gh-action-pypi-publish
- **Test matrix**: Python 3.11, 3.12, 3.13
- **Artifact upload**: Distributions attached to GitHub Release

### ✅ Safety Features
- Tests must pass before publishing
- Environment protection (manual approval if configured)
- Skip existing packages (won't fail if version exists)
- Verbose output for debugging

### ✅ Flexibility
- Manual trigger via workflow_dispatch
- Separate TestPyPI and PyPI environments
- Support for both Trusted Publisher and API tokens

## Troubleshooting

### Issue: "Invalid or non-existent authentication information"

**Cause:** Trusted Publisher not configured or API token missing

**Solution:**
1. Check PyPI Trusted Publisher settings
2. Or add `PYPI_API_TOKEN` secret to GitHub environment

### Issue: "File already exists"

**Cause:** Version already published to PyPI

**Solution:**
1. Bump version in `pyproject.toml`
2. Create new tag
3. Re-publish

### Issue: "Tests failed"

**Cause:** CI tests must pass before publishing

**Solution:**
1. Fix failing tests
2. Push fixes
3. Re-create release

## Benefits of Trusted Publisher

| Feature | API Token | Trusted Publisher (OIDC) |
|---------|-----------|--------------------------|
| Security | Long-lived token | Short-lived, auto-rotating |
| Setup | Manual token management | One-time PyPI config |
| Rotation | Manual | Automatic |
| Scope | Project or account-wide | Workflow-specific |
| Revocation | Manual | Automatic on workflow change |
| Audit | Limited | Full GitHub Actions audit trail |

**Recommendation:** Use Trusted Publisher for production.

## Maintenance

### Updating the Workflow

1. Edit `.github/workflows/deploy_pypi.yml`
2. Test with TestPyPI first (create prerelease)
3. Verify on test.pypi.org
4. Deploy to production PyPI

### Monitoring

```bash
# Check workflow runs
gh run list --workflow deploy_pypi.yml --limit 5

# View specific run
gh run view <run_id> --log

# Check PyPI package
https://pypi.org/project/kagura-ai/
```

---

**For more information:**
- PyPI Trusted Publishers: https://docs.pypi.org/trusted-publishers/
- uv Publishing: https://docs.astral.sh/uv/guides/publish/
- GitHub Actions: https://docs.github.com/actions
