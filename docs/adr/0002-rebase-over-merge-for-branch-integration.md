# ADR-0002: Rebase Over Merge for Branch Integration

## 📋 Status

Accepted
- 📅 Date      : 25-06-2026
- 👷 Authors   : JG
- 👀 Reviewers : Transcendence Team

---

## 🧭 Context And Problem

When a feature branch needs to incorporate upstream changes from `main`, or when
it is ready to be integrated, there are two primary strategies: merge and rebase.
The choice has a direct and lasting impact on the readability of the commit history.

With multiple developers committing in parallel, a merge-heavy workflow produces
a history full of interleaved merge commits that obscure the logical progression
of each feature.

---

## 🎯 Decision Drivers

* Commit history must be linear and readable (`git log` should tell a story)
* `main` history must never be rewritten
* Conflicts must be resolved locally before integration, not post-merge
* The chosen approach must be safe for collaborative branches

---

## 💡 Considered Options

### Option 1: Merge (merge commits)

> Integrate branches with `git merge`, producing an explicit merge commit.

- 📝 **More details**: Default Git behavior. Creates a merge commit recording
  the convergence of two branch histories.
- ✅ **Advantages**:
  - Non-destructive — original branch history is preserved exactly
  - No force-push required
  - Familiar to most developers
- 🚫 **Disadvantages**:
  - Produces a non-linear history full of merge commits
  - `git log --oneline` becomes hard to read at scale
  - Harder to `git bisect` or isolate regressions

---

### Option 2: Rebase ⭐ *(chosen)*

> Synchronize feature branches with `git rebase main` before integration;
> merge into `main` as a fast-forward.

- 📝 **More details**: Rebase replays feature commits on top of the current tip
  of `main`, producing a linear history. The merge into `main` becomes a
  fast-forward — no merge commit is created.
- ✅ **Advantages**:
  - Linear, readable commit history on `main`
  - Conflicts surfaced and resolved per-commit during rebase — easier to isolate
  - `git log`, `git bisect`, and rollbacks all work cleanly
- 🚫 **Disadvantages**:
  - Requires `--force-with-lease` after rebasing a pushed branch
  - Slightly steeper learning curve than plain merge
  - Must never rebase commits already present on `main`

---

### Option 3: Squash and merge

> Squash all commits from a feature branch into one before merging into `main`.

- 📝 **More details**: Used by some teams to keep `main` extremely clean,
  one commit per feature.
- ✅ **Advantages**:
  - `main` log is extremely concise
  - Noisy WIP commits are hidden
- 🚫 **Disadvantages**:
  - Destroys granular commit history — individual steps of a feature are lost
  - Makes `git bisect` less useful within a feature's scope
  - Authorship of individual commits is collapsed

---

## ✅ Decision

**We use rebase to synchronize feature branches with `main` before integration.**

Implementation details:
- Before merging, always rebase the feature branch on the latest `main`:
```bash
  git checkout main && git pull origin main
  git checkout <feature-branch>
  git rebase main
```
- After rebasing a pushed branch, update the remote with:
```bash
  git push --force-with-lease
```
- `git push --force` is **strictly prohibited** — it can silently overwrite
  collaborators' commits
- To undo a faulty commit on `main`, use `git revert` — never `git reset`

---

## 🔄 Consequences

### 🟢 Positive

* `git log --oneline` on `main` reads as a clean, chronological feature list
* Regressions are easier to locate with `git bisect`
* Conflicts are resolved in context (per commit) rather than all at once

### 🔴 Negative

* Force-pushing rebased branches is necessary — team must understand
  `--force-with-lease` vs `--force`
* Rebase rewrites commit hashes — collaborators on the same feature branch
  must re-sync after a rebase

### 📌 Required Actions

1. [ ] Brief the team on `git rebase` vs `git merge` — one short session
2. [ ] Add `--force-with-lease` reminder to the git workflow reference doc
3. [ ] Confirm no CI pipeline relies on merge commit presence

---

## 🔗 Links

* Branching strategy: `ADR-0001`
* Commit convention: `ADR-0003`
