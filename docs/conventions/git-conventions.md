# Git Conventions

## Purpose

This document defines the Git rules and conventions used by the
Transcendence team.

It describes:

- Branch naming rules
- Branch lifecycle
- Protected branch rules
- Git safety rules

The reasons behind these choices are documented in:

- ADR-0001 — Branching Strategy
- ADR-0002 — Rebase Over Merge

---

# Branch Strategy

The project uses a feature branch workflow.

Rules:

- `main` is the stable integration branch.
- Direct commits to `main` are prohibited.
- All changes must happen through dedicated branches.
- Branches should represent one focused objective.

---

# Branch Naming Convention

Branch names must communicate the purpose of the branch.

Format:

```text
<type>/<ticket-id>-<short-description>
```

Example:

```text
feature/TR-123-user-authentication

bugfix/TR-456-login-validation

hotfix/TR-789-security-patch
```

---

# Branch Types

| Prefix | Usage | Example |
|---|---|---|
| `feature/` | New functionality | `feature/TR-123-profile-page` |
| `bugfix/` | Fix existing behavior | `bugfix/TR-456-token-error` |
| `hotfix/` | Urgent production fix | `hotfix/TR-789-security-patch` |
| `docs/` | Documentation changes | `docs/update-architecture` |
| `chore/` | Maintenance/tooling | `chore/update-dependencies` |

---

# Branch Lifecycle

A branch should:

1. Be created from the latest `main`.
2. Represent one task or objective.
3. Be kept short-lived.
4. Be deleted after successful integration.

---

# Main Branch Rules

The `main` branch is protected.

Rules:

- No direct pushes.
- No history rewriting.
- Changes require review before integration.

---

# History Rewriting Rules

After rebasing a pushed branch:

```bash
git push --force-with-lease
```

## Why not `git push --force`?

`--force` can overwrite commits pushed by another contributor.

`--force-with-lease` verifies that the remote branch has not changed before
updating it.


---

# Related Documentation

- `git-workflow.md` — Daily Git operations
- `commits.md` — Commit message rules
- ADR-0001 — Branching Strategy
- ADR-0002 — Rebase Over Merge
