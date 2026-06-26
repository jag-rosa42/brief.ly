# ADR-0001: Branching Strategy

## 📋 Status

Accepted
- 📅 Date      : 25-06-2026
- 👷 Authors   : JG
- 👀 Reviewers : Transcendence Team

---

## 🧭 Context And Problem

The team works concurrently on multiple features across several services
(backend, frontend, AI pipeline, infrastructure). Without a defined branching
strategy, the following risks emerge:

1. **Unstable main**: unfinished work mixed with production-ready code
2. **Integration chaos**: no clear moment or process to reconcile parallel work
3. **Unclear ownership**: ambiguity over which branch to branch from or merge into

---

## 🎯 Decision Drivers

* `main` must always reflect production-ready, deployable code
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

> Full Gitflow with `main`, `develop`, `release/*`, `feature/*`, and `hotfix/*`.

- 📝 **More details**: A formalized workflow designed for versioned release cycles.
- ✅ **Advantages**:
  - Clear separation between development and production
  - Supports parallel release preparation
- 🚫 **Disadvantages**:
  - Heavy overhead for a team without a formal release cycle
  - `develop` branch adds indirection without value at our scale
  - Cognitive overhead disproportionate to team size

---

### Option 3: Feature branch workflow ⭐ *(chosen)*

> All work happens in short-lived feature branches; `main` is the single
> integration target and always stays deployable.

- 📝 **More details**: Each branch maps to one ticket/objective and is deleted
  after merge. Branch type is encoded in the name prefix.
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

**We adopt a feature branch workflow where `main` is always production-ready
and all work is developed in typed, ticket-scoped branches.**

Implementation details:
- `main` is protected — direct pushes are prohibited
- Branch naming convention:
	- feature/<ticket-id>-<short-description>
	- bugfix/<ticket-id>-<short-description>
	- hotfix/<ticket-id>-<short-description>
- Branches are deleted after successful merge
- See ADR-0002 for the integration strategy (rebase policy)

---

## 🔄 Consequences

### 🟢 Positive

* `main` can be deployed or demonstrated at any time
* Each branch has a clear scope, reducing review complexity
* Branch history is self-documenting through naming conventions

### 🔴 Negative

* Team must internalize the naming convention — inconsistency breaks readability
* Feature branches that live too long require more rebase effort (mitigated by ADR-0002)

### 📌 Required Actions

1. [ ] Enable branch protection on `main`
2. [ ] Share naming convention with the full team
3. [ ] Delete merged branches consistently (can be automated on the Git host)

---

## 🔗 Links

* Integration policy: `ADR-0002`
