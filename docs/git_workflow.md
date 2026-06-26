# Classical Development Git Workflow

## Feature Development Workflow

1. Create and switch to a new branch:

```bash
git checkout -b <branch-name>
```

or

```bash
git switch -c <branch-name>
```

2. Implement the required changes.

3. Stage modified files:

```bash
git add <file-name>
```

4. Create a commit:

```bash
git commit -m "<commit-message>"
```

5. Push the branch to the remote repository:

```bash
git push -u origin <branch-name>
```

Subsequent pushes can be performed with:

```bash
git push
```

---

## Synchronizing a Feature Branch with Main

Before merging, the feature branch must be rebased on the latest version of `main`.

### Update the local main branch

```bash
git checkout main
git pull origin main
```

### Switch back to the feature branch

```bash
git checkout <feature-branch-name>
```

### Rebase feature branch on top of main

```bash
git rebase main
```

### If conflicts occur

Resolve conflicts manually, then:

```bash
git add <resolved-files>
git rebase --continue
```

Repeat until the rebase completes successfully.

### Update the remote feature branch

```bash
git push --force-with-lease
```

> Never use:
>
> ```bash
> git push --force
> ```
>
> Always use:
>
> ```bash
> git push --force-with-lease
> ```
>
> to prevent overwriting other contributors' work.

---

## Merging feature-branch into Main

After the branch is successfully rebased and validated:

### Update local main

```bash
git checkout main
git pull origin main
```

### Merge the feature branch

```bash
git merge <feature-branch-name>
```

### Alternative: merge only specific commits

```bash
git cherry-pick <commit-hash>
```

### Push the updated main branch

```bash
git push origin main
```

---

## Reverting Changes on Main

If a commit introduced a regression or issue, create a revert commit rather than rewriting history.

### Revert a commit

```bash
git revert <commit-hash>
```

### Push the revert commit

```bash
git push origin main
```

This preserves repository history while safely undoing the change.
