# Branch Management Policy for Kagura-AI

## 🎯 Overview

This document defines the branch management strategy for Kagura-AI to ensure code quality, maintainability, and efficient collaboration.

---

## 📝 Branch Naming Convention

### Required Pattern

**Standard Format**:
```
{issue-number}-{type}/{description}
```

**Examples**:
```
565-fix/integration-tests-python-version
550-feat/cli-utilities-consolidation
563-docs/v4.1.0-cleanup
556-feat/hippocampus-memory-phase1
```

### Components

#### Issue Number (Required)
- Must correspond to a GitHub Issue
- Use `gh issue develop {issue-number} --checkout` to auto-create branch
- Links commits to issue context

#### Type (Required)
- `feat` - New feature
- `fix` - Bug fix
- `docs` - Documentation only
- `chore` - Maintenance (dependencies, config)
- `refactor` - Code refactoring
- `test` - Test improvements
- `perf` - Performance improvements

#### Description (Required)
- 2-5 words maximum
- kebab-case (lowercase with hyphens)
- Clear and concise
- No special characters except hyphens

### Exception: Urgent Fixes

For **critical hotfixes** without existing issues:
```
{type}/{description}

Example:
hotfix/critical-pypi-publish
```

**Note**: Create GitHub Issue immediately after hotfix is deployed.

---

## 🔄 Branch Lifecycle

### 1. Creation

**Recommended**:
```bash
# Create issue first
gh issue create --title "Fix integration tests" --label "bug"

# Create branch from issue
gh issue develop 565 --checkout
```

**Manual** (if needed):
```bash
git checkout -b 565-fix/integration-tests
```

### 2. Development

- **Max lifespan**: 7 days
- **Sync frequency**: Daily with main
- **Commits**: Small, atomic, well-described
- **Tests**: Run locally before push

**Daily sync**:
```bash
git fetch origin
git rebase origin/main  # For solo branches
# OR
git merge origin/main   # For collaborative branches
```

### 3. Pull Request

**Before creating PR**:
- [ ] All tests passing locally
- [ ] Branch up-to-date with main
- [ ] Commit messages follow Conventional Commits
- [ ] Documentation updated if needed

**Create PR**:
```bash
gh pr create --title "feat(scope): Description" --body "..."
```

### 4. Review & Merge

**Requirements** (enforced by branch protection):
- [ ] At least 1 approval (if team >1)
- [ ] All CI checks passing
- [ ] Branch up-to-date with main
- [ ] All conversations resolved

**Merge strategy**:
- **Squash merge**: feat, fix, docs, chore, refactor, test, perf
- **Merge commit**: release branches only (rare)

```bash
gh pr merge {PR} --squash
```

### 5. Deletion

**Automatic**: GitHub auto-deletes after merge (if enabled)

**Manual** (if needed):
```bash
# Delete remote branch
git push origin --delete {branch-name}

# Delete local branch
git branch -D {branch-name}
```

---

## 🚫 Prohibited Practices

### Never Do This

1. **Direct commits to main**
   - Always create a PR, even for docs
   - Branch protection enforces this

2. **Long-lived branches**
   - Max 7 days
   - If longer needed, break into smaller PRs

3. **Inconsistent naming**
   - Follow the pattern strictly
   - Use `gh issue develop` to avoid mistakes

4. **Force push to main**
   - Absolutely forbidden
   - Will be rejected by branch protection

5. **Merge commits in feature branches**
   - Prefer rebase for cleaner history
   - Merge commits only for collaborative work

---

## 🏷️ Special Branch Types

### Release Branches (Rare)

**Only create for LTS releases**:
```
release/v4.0-lts    # Long-term support for v4.0.x
release/v4.1-lts    # Long-term support for v4.1.x
```

**Standard releases**: Use tags only, no branch needed
```bash
git tag v4.2.0
git push origin v4.2.0
gh release create v4.2.0
```

### Hotfix Branches

For production emergencies:
```
hotfix/{critical-description}

Example:
hotfix/pypi-publish-failure
```

**Workflow**:
1. Create hotfix branch
2. Fix immediately
3. Create PR with `urgent` label
4. Fast-track review
5. Create issue retrospectively

---

## 🧹 Branch Cleanup

### Automated Cleanup

**GitHub Setting**:
- Settings → General → Pull Requests
- ☑ Automatically delete head branches

### Manual Cleanup (Weekly)

**Find merged branches**:
```bash
git fetch --prune
git branch -r --merged origin/main | grep -v "main\|HEAD"
```

**Delete obsolete branches**:
```bash
# Remote
git push origin --delete {branch-name}

# Local
git branch -D {branch-name}
```

**Clean up local references**:
```bash
git fetch --prune
git branch -vv | grep '\[origin.*gone\]' | awk '{print $1}' | xargs git branch -D
```

---

## 📊 Branch Health Metrics

Track these metrics monthly:

- **Active branches**: Should be ≤ 10
- **Average branch age**: Should be ≤ 5 days
- **Orphaned branches**: Should be 0
- **Naming compliance**: Should be 100%
- **CI pass rate**: Should be 100% before merge

---

## 🔗 Related Documentation

- **CLAUDE.md**: Development workflow
- **CONTRIBUTING.md**: Contribution guidelines
- **GitHub Issues**: https://github.com/JFK/kagura-ai/issues
- **Pull Requests**: https://github.com/JFK/kagura-ai/pulls

---

## 🆘 Troubleshooting

### "Can't push to main"
- **Expected**: Main is protected
- **Solution**: Create a feature branch and PR

### "Branch name invalid"
- **Check**: Does it match `{issue}-{type}/{desc}` pattern?
- **Fix**: Rename branch: `git branch -m new-name`

### "Branch diverged from main"
- **Solution**: Rebase onto main
  ```bash
  git fetch origin
  git rebase origin/main
  git push --force-with-lease
  ```

### "Too many branches"
- **Solution**: Run weekly cleanup script
- **Prevention**: Enable auto-delete

---

**Last Updated**: 2025-11-05
**Version**: 4.1.0
**Status**: Active Policy
