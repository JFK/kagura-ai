# Branch Management Policy

## 🎯 Branch Strategy (v4.1.1+)

### Release Branch Workflow

```
main (stable, tagged releases only)
  ↑
v4.x.x-release (release branch) ← Collect features here
  ↑         ↑         ↑
#548    #555    #411  (feature branches)
```

**Process**:
1. **Create release branch** from main: `git checkout -b v4.1.1-release`
2. **Merge feature PRs** into release branch (not main)
3. **Test thoroughly** on release branch
4. **Merge to main** when ready: `git checkout main && git merge v4.1.1-release`
5. **Tag release**: `git tag v4.1.1 && git push --tags`

**Benefits**:
- ✅ Isolate main from WIP features
- ✅ Easy rollback of problematic features
- ✅ Parallel development on multiple versions
- ✅ Clear release checkpoints

---

## 📝 Branch Naming Convention

### Feature/Fix Branches

**Recommended format** (enforced by CI):
```
{issue-number}-{type}/{short-description}
```

**Examples**:
```
548-perf/cli-startup
555-refactor/cli-structure
563-docs/api-reference
```

**Create from GitHub Issue**:
```bash
gh issue develop 548 --checkout
# → Creates: 548-{type}/{auto-generated-description}
```

### Release Branches

```
v{major}.{minor}.{patch}-release

Examples:
v4.1.1-release
v4.2.0-release
v5.0.0-release
```

### Hotfix Branches (Emergency Only)

For **critical production bugs** without existing issues:
```
hotfix/{short-description}

Example:
hotfix/pypi-publish-failure
```

**⚠️ Important**: Create GitHub Issue immediately after hotfix.

---

## 🔄 Workflow Examples

### Standard Feature Development

```bash
# 1. Create issue
gh issue create --title "Optimize CLI startup" --label "performance"

# 2. Create branch from issue
gh issue develop 548 --checkout

# 3. Implement feature
git commit -m "perf(cli): Optimize startup time"

# 4. Push and create PR targeting release branch
git push -u origin 548-perf/cli-startup
gh pr create --base v4.1.1-release --draft

# 5. Ready for review
gh pr ready 548

# 6. Merge into release branch (via GitHub or CLI)
gh pr merge 548 --squash
```

### Release Process

```bash
# 1. All features merged into v4.1.1-release
# 2. Final testing on release branch
pytest -n auto

# 3. Update version and changelog
# Edit: pyproject.toml, CHANGELOG.md

# 4. Merge to main
git checkout main
git merge v4.1.1-release --no-ff -m "Release v4.1.1"

# 5. Tag and push
git tag v4.1.1
git push origin main --tags

# 6. Publish to PyPI (CI handles this automatically on tag push)
```

---

## ⚙️ CI/CD Integration

### Branch Protection

**.github/workflows/branch-protection.yml**:
- ✅ Allows: `{number}-{type}/{description}` (e.g., `548-perf/cli-startup`)
- ✅ Allows: `v{version}-release` (e.g., `v4.1.1-release`)
- ✅ Allows: `hotfix/{description}` (emergency only)
- ✅ Allows: Legacy patterns for compatibility (e.g., `{number}-{type}-{description}`)
- ❌ Blocks: Random branch names

**Enforcement**:
- Runs on every push
- Fails CI if branch name doesn't match pattern
- Clear error message with correct format

### Auto-Merge Rules

- **Release branches**: Require 0 approvals (maintainer can merge freely)
- **Feature branches**: Require 1 approval (optional, can be disabled)
- **Main branch**: Protected, only accept merges from release branches

---

## 🏷️ Branch Types

| Type | Purpose | Example | Merge Target |
|------|---------|---------|--------------|
| `feat` | New feature | `555-feat/cli-wizard` | Release branch |
| `fix` | Bug fix | `548-fix/session-bug` | Release branch |
| `perf` | Performance | `548-perf/cli-startup` | Release branch |
| `refactor` | Refactoring | `555-refactor/cli` | Release branch |
| `docs` | Documentation | `563-docs/api-ref` | Release branch or main |
| `test` | Testing | `570-test/e2e` | Release branch |
| `chore` | Maintenance | `571-chore/deps` | Release branch or main |
| `hotfix` | Emergency | `hotfix/critical-bug` | Main (then backport) |

---

## 📦 Release Branch Lifecycle

### Phase 1: Development (1-2 weeks)
- Create release branch: `v4.1.1-release`
- Merge features as they complete
- Continuous testing

### Phase 2: Feature Freeze (2-3 days)
- No new features
- Bug fixes only
- Final integration testing

### Phase 3: Release (1 day)
- Merge to main
- Tag version
- Publish to PyPI
- Close milestone

### Phase 4: Cleanup
- Delete release branch (optional, keep for reference)
- Archive completed issues
- Plan next milestone

---

## 🚨 Exceptions & Edge Cases

### Working on Multiple Versions

```bash
# Working on v4.1.1 and v4.2.0 simultaneously
git checkout v4.1.1-release
git merge 548-perf/cli-startup

git checkout v4.2.0-release
git merge 555-feat/new-feature
```

### Hotfix to Released Version

```bash
# Main is at v4.1.1
git checkout -b hotfix/critical-bug main
# Fix bug
git checkout main
git merge hotfix/critical-bug --no-ff
git tag v4.1.2
git push --tags

# Backport to release branch if needed
git checkout v4.2.0-release
git cherry-pick <hotfix-commit>
```

### Abandoned Branches

- Delete after 30 days of inactivity
- Archive issue as "wontfix" or "deferred"

---

## 📚 Migration from Old Policy

### Old Policy (v4.0)
- ❌ All PRs target main
- ❌ Strict naming: `{number}-{type}/{desc}` only
- ❌ No hotfix exception

### New Policy (v4.1.1+)
- ✅ PRs target release branch
- ✅ Flexible naming: Legacy patterns allowed
- ✅ Hotfix exception for emergencies

**No action required**: Existing branches are grandfathered in.

---

## 🔗 References

- [Semantic Versioning](https://semver.org/)
- [Git Flow](https://nvie.com/posts/a-successful-git-branching-model/)
- [GitHub Flow](https://guides.github.com/introduction/flow/)
- [Conventional Commits](https://www.conventionalcommits.org/)

---

**Last Updated**: 2025-11-06 (v4.1.1 milestone)
**Maintained By**: @JFK
