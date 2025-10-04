# Release Process

## Automated Release (Recommended)

When you create a GitHub Release, the `deploy_pypi.yml` workflow automatically:
1. Runs all tests and checks
2. Builds the package
3. Publishes to PyPI (for full releases) or TestPyPI (for prereleases)

**Steps**:
1. Update version in `pyproject.toml` and `src/kagura/version.py`
2. Update `CHANGELOG.md` with release notes
3. Commit and push changes
4. Create GitHub Release: `gh release create vX.Y.Z --title "vX.Y.Z - Title" --notes "Release notes"`
5. GitHub Actions will automatically publish to PyPI

## Manual Release (Alternative)

If you need to publish manually (e.g., automated workflow fails):

**Prerequisites**:
- Configure `~/.pypirc` with PyPI API token:
  ```ini
  [pypi]
  username = __token__
  password = pypi-AgEIcH...
  ```

**Steps**:
1. Update version in `pyproject.toml` and `src/kagura/version.py`
2. Update `CHANGELOG.md` with release notes
3. Commit and push changes
4. Build package: `uv build`
5. Upload to PyPI: `twine upload dist/kagura_ai-X.Y.Z*`
6. Create GitHub Release: `gh release create vX.Y.Z --title "vX.Y.Z - Title" --notes "Release notes"`

## Major or Minor Release

1. Create a release branch named `vX.Y.Z` where `X.Y.Z` is the version.
2. Bump version number on release branch.
3. Create an annotated, signed tag: `git tag -s -a vX.Y.Z`
4. Create a github release using `gh release create` and publish it.
5. Have the release flow being reviewed.
7. Bump version number on `main` to the next version followed by `.dev`, e.g. `v0.4.0.dev`.

## Test Release
Create a release branch named `vX.Y.Z` where `X.Y.Z` is the version as a pre-release.
GitHub Actions will publish the package to Test PyPI.

### Install Test Release

```bash
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ kagura-ai
```
