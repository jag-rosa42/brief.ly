# Git Workflow

## 1. Purpose

This document describes the daily Git workflow used by the Transcendence team.

It explains the steps required to:

- Create a development branch.
- Implement changes.
- Synchronize with `main`.
- Prepare changes for integration.

Rules and conventions are documented separately:

- `git-conventions.md` → Git rules and branch conventions.
- `git-commits.md` → Commit message convention.

Architectural decisions:

- ADR-0001 → Branching Strategy.
- ADR-0002 → Rebase Over Merge.
- ADR-0003 → Commit Message Convention.

---

## 2. Creating a Feature Branch

### 2.1 Update Local Main

Always start from the latest version of `main`.

```bash
git checkout main
git pull origin main
```

---

### 2.2 Create a New Branch

Create a branch following the naming convention defined in:

```
git-conventions.md
```

Example:

```bash
git switch -c feature/TR-123-user-authentication
```

---

## 3. Developing Changes

Implement the required changes.

Before committing:

- Verify the changes are related to the branch objective.
- Run relevant tests.
- Remove unnecessary modifications.

---

## 4. Creating Commits

Stage changes:

```bash
git add <files>
```

Create a commit following:

```
commits.md
```

Example:

```bash
git commit -m "✨ [auth] add JWT refresh endpoint"
```

---

## 5. Publishing the Branch

Push the branch for the first time:

```bash
git push -u origin <branch-name>
```

For subsequent pushes:

```bash
git push
```

---

## 6. Synchronizing With Main

Before requesting integration, update the branch with the latest changes
from `main`.

### 6.1 Update Main

```bash
git checkout main
git pull origin main
```

---

### 6.2 Return To Feature Branch

```bash
git checkout <feature-branch-name>
```

---

### 6.3 Rebase Feature Branch

```bash
git rebase main
```

This reapplies the feature commits on top of the latest `main`.

---

## 7. Resolving Rebase Conflicts

If conflicts occur:

1. Resolve the conflicting files.
2. Stage the resolved files:

```bash
git add <resolved-files>
```

3. Continue the rebase:

```bash
git rebase --continue
```

Repeat until the rebase completes.

---

## 8. Updating a Rebasing Branch

Because rebasing changes commit history, the remote branch must be updated
using:

```bash
git push --force-with-lease
```

Never use:

```bash
git push --force
```

`--force-with-lease` protects against accidentally overwriting another
contributor's changes.

---

## 9. Integration Workflow

After:

- The branch has been rebased.
- Tests pass.
- Changes have been reviewed.

The branch can be integrated into `main`.

The integration process must preserve the linear history defined in ADR-0002.

---

## 10. Reverting Changes

Shared history must not be rewritten.

If an integrated change introduces a problem:

```bash
git revert <commit-hash>
```

Push the revert commit:

```bash
git push origin main
```

This creates a new commit that safely reverses the previous change.

---

## 11. Complete Workflow Summary

```text
main
 |
 | update
 |
 v
feature/TR-123-description
 |
 | develop changes
 |
 | commit using Gitmoji
 |
 | push branch
 |
 | rebase with latest main
 |
 | resolve conflicts if needed
 |
 | review
 |
 v
main
```

---

## 12. Related Documentation

- `git-conventions.md`
- `commits.md`

Related ADRs:

- ADR-0001 — Branching Strategy
- ADR-0002 — Rebase Over Merge
- ADR-0003 — Commit Message Convention
