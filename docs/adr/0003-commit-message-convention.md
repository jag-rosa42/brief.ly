# ADR-0003: Commit Message Convention (Conventional Commits)

## 📋 Status

Accepted
- 📅 Date      : 25-06-2026
- 👷 Authors   : JG
- 👀 Reviewers : Transcendence Team

---

## 🧭 Context And Problem

Commit messages are the primary documentation layer of the codebase's evolution.
Without a shared convention, messages vary wildly in quality and format across
contributors, making the history harder to read, search, and reason about.

Observed failure modes without a convention:
1. **Uninformative messages**: `fix`, `update`, `changes`, `stuff`
2. **Inconsistent scope**: some messages describe files changed, others describe intent
3. **No machine-readability**: changelog generation and semantic versioning
   tooling cannot parse free-form messages

---

## 🎯 Decision Drivers

* Messages must communicate *what changed and why* at a glance
* Convention must be simple enough to follow without tooling enforcement
* Should be compatible with automated changelog generation if adopted later
* Must be consistent across all contributors

---

## 💡 Considered Options

### Option 1: Free-form messages with guidelines

> No enforced format — just a written guideline asking for "clear and
> descriptive" messages.

- 📝 **More details**: Document a list of good/bad examples and rely on
  code review to enforce quality.
- ✅ **Advantages**:
  - No tooling required
  - Maximum flexibility per commit
- 🚫 **Disadvantages**:
  - Inconsistency across contributors is virtually guaranteed
  - No machine-readable structure — automation impossible
  - "Clear and descriptive" is subjective and degrades under deadline pressure

---

### Option 2: Conventional Commits ⭐

> Adopt the [Conventional Commits](https://www.conventionalcommits.org)
> specification: `<type>(<scope>): <short description>`.

- 📝 **More details**: A lightweight, widely adopted specification that
  structures commit messages around a type prefix. Types include `feat`, `fix`,
  `refactor`, `docs`, `test`, `chore`, `ci`, and others.
- ✅ **Advantages**:
  - Immediately communicates the nature of a change from the type prefix
  - Machine-readable — compatible with `semantic-release`, `git-cliff`, etc.
  - Industry standard — familiar to most developers
  - Easy to learn: one line of format, a handful of types
- 🚫 **Disadvantages**:
  - Requires the team to internalize the type vocabulary
  - Slightly more friction than typing a free-form message
  - Scope field can become inconsistent without a defined scope list

---

### Option 3: Gitmoji *(chosen)*

> Prefix every commit message with a relevant emoji to convey type visually.
> specification: `<gitmoji> [scope] <short description>`.
- 📝 **More details**: `🐛 [authentication] fix login validation`, `✨ [authentication] add JWT auth`.
- ✅ **Advantages**:
  - Visually distinctive in log output
  - Fun and expressive
- 🚫 **Disadvantages**:
  - Emoji set is large and subjective — teams frequently disagree on the right one
  - Not natively machine-readable without custom tooling
  - Can appear unprofessional in evaluation or external contexts

---

## ✅ Decision

**We adopt the Gitmoji specification for all commit messages.**

Implementation details:
- Format: `<gitmoji> [<scope>] <short description>`.
- Approved types:

  | Type | When to use                                      |
  |------|--------------------------------------------------|
  | ✨   | A new feature                                    |
  | 🐛   | A bug fix                                        |
  | ♻️   | Code change that is neither a fix nor a feature  |
  | 📝   | Documentation only                               |
  | ✅   | Adding or updating tests                         |
  | 🔧   | Build process, dependency updates, tooling       |
  | 👷   | CI/CD pipeline changes                           |
  | ⚡️   | Performance improvement                          |

- Examples:
	- ✨ [auth] add JWT token refresh endpoint
	- 🐛 [parser] resolve off-by-one in Content-Length handling
	- 📝 [adr] add ADR-0003 commit convention
	- 🔧 [deps] upgrade FastAPI to 0.111.0
---

## 🔄 Consequences

### 🟢 Positive

* `git log --oneline` becomes a structured changelog at a glance
* gitmoji prefix instantly signals the nature and risk level of a change
* Enables automated changelog and release note generation if needed later

### 🔴 Negative

* Team must learn and consistently apply the gitmoji vocabulary
* Scope definitions may require a follow-up decision if ambiguity arises

### 📌 Required Actions

1. [ ] Share this ADR and the type table with the full team
2. [ ] Add commit examples to `/docs/git-workflow.md`
3. [ ] (Optional) Add a `commitlint` CI step to enforce format on push

---

## 🔗 Links

* Conventional Commits spec: https://www.conventionalcommits.org
* Workflow reference: `/docs/git-workflow.md`
* Branching strategy: `ADR-0001`
* Integration policy: `ADR-0002`
