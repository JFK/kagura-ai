# Release Process

## Major or Minor Release

1. Create a release branch named `vX.Y.Z` where `X.Y.Z` is the version.
2. Bump version number on release branch.
3. Create an annotated, signed tag: `git tag -s -a vX.Y.Z`
4. Create a github release using `gh release create` and publish it.
5. Have the release flow being reviewed.
7. Bump version number on `main` to the next version followed by `.dev`, e.g. `v0.4.0.dev`.

## Test Release
Create a release branch named `vX.Y.Z` where `X.Y.Z` is the version as a pre-release.
GithHub Aactions will publish the package to Test PyPI.

### Install Test Release

```bash
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ kagura-ai
```
