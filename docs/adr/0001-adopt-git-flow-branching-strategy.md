# ADR-0001: Branching Strategy

## 📋 Status

Accepted
- 📅 Date      : 25-06-2026
- 👷 Authors   : JG
- 👀 Reviewers : Transcendence Team

---

## 🧭 Context And Problem

The team works concurrently on multiple features across several services
(backend, frontend, AI pipeline, infrastructure).

Without a defined branching strategy, the following risks emerge:

1. **Unstable main**: unfinished work mixed with production-ready code
2. **Integration chaos**: no clear moment or process to reconcile parallel work
3. **Unclear ownership**: ambiguity over which branch to branch from or merge into

---

## 🎯 Decision Drivers

* `main` must always reflect stable, production-ready, deployable code
* Parallel feature development must be isolated until validated
* Branch purpose must be immediately readable from its name
* Strategy must be simple enough for all team members to follow without tooling

---

## 💡 Considered Options

### Option 1: Direct commits to main

> Everyone commits directly to `main`, no branches.

- 📝 **More details**: Common in solo projects or very small teams.
- ✅ **Advantages**:
  - Zero branching overhead
  - No merge or rebase steps
- 🚫 **Disadvantages**:
  - A single broken commit destabilizes the entire team
  - No isolation for in-progress work
  - Impossible to review changes before integration

---

### Option 2: Gitflow (main + develop + release branches)

> Use the full Gitflow branching model

- 📝 **More details**: A structured workflow with dedicated branches for development, releases,
  features and hotfixes.
- ✅ **Advantages**:
  - Clear separation between development and production
  - Supports parallel release preparation
- 🚫 **Disadvantages**:
  - Heavy overhead for a team without a formal release cycle
  - `develop` branch adds indirection without value at our scale
  - Cognitive overhead disproportionate to team size

---

### Option 3: Feature branch workflow ⭐ *(chosen)*

> All work happens in short-lived feature branches;
> `main` is the single integration target and always stays deployable.

- 📝 **More details**: Each branch represents one focused change and is integrated after validation.
- ✅ **Advantages**:
  - `main` is always stable
  - Isolation per feature enables parallel work without interference
  - Branch names carry intent at a glance
  - Simple mental model — one rule: never commit directly to `main`
- 🚫 **Disadvantages**:
  - Requires discipline to keep branches short-lived and focused
  - Long-running branches accumulate drift and become costly to integrate

---

## ✅ Decision

**We adopt a feature branch workflow where `main` remains the stable integration
branch and all changes are developed in isolated branches.**

The operational workflow, branch naming rules, and branch lifecycle are
documented in:

`/docs/conventions/git-workflow.md`

Integration rules are documented in:

`ADR-0002: Rebase Over Merge for Branch Integration`

---

## 🔄 Consequences

### 🟢 Positive

* `main` remains stable and ready for demonstration or deployment
* Changes are isolated before integration
* Pull requests provide a clear review boundary
* Branch purpose remains explicit

### 🔴 Negative

* Team must internalize the naming convention — inconsistency breaks readability
* Feature branches that live too long require more rebase effort (mitigated by ADR-0002)

### 📌 Required Actions

1. [ ] Enable branch protection on `main`
2. [ ] Document branch workflow in `/docs/conventions/git-workflow.md`
3. [ ] Ensure contributors understand feature branch usage

---

## 🔗 Links

* Git workflow: `/docs/conventions/git-workflow.md`
* Integration policy: `ADR-0002`
* Commit convention: `ADR-0003`

