# ADR-0000: Use ADR for Architectural Decision Tracking

## Status

Accepted
- 📅 Date     : 24-06-2026
- 👷 Authors  : JG
- Reviewers   : Transcendence Team

## Context And Problem

The Transcendence project involves a team of multiple developers working across
complex technical domains (backend, frontend, AI/RAG pipeline, infrastructure).
Without a structured process, the reasoning behind architectural and methodology
decisions tends to be lost over time — leaving future contributors (or current
ones, weeks later) unable to understand *why* a choice was made.

Key pain points observed:
1. **Lost rationale**: decisions made in verbal discussions leave no written trace
2. **Onboarding friction**: new team members lack context on existing choices
3. **Revisited debates**: the same trade-offs get re-argued because no record exists
4. **Presentation quality**: team demos and evaluations suffer when decisions
   can't be clearly justified

## Decision Drivers

* Preserve architectural and methodology decision rationale close to the codebase
* Keep the process lightweight enough that the team actually uses it
* Avoid dependency on external tools (Notion, Confluence) that could become
  unavailable or siloed
* Enable automation through CI (linting, format validation, status checks)
* Support async review — any team member can comment on an ADR via pull request

## Considered Options

### Option 1: Notion

Centralize all decision documentation in a shared Notion workspace.

- **More details**: Create a dedicated Notion database with structured properties
  (status, date, authors, tags). Each decision is a Notion page.
- ✅ **Advantages**:
  - Rich formatting, inline comments, easy for non-technical contributors
  - Notion AI can assist in drafting
  - No Git knowledge required to contribute
- 🚫 **Disadvantages**:
  - Decoupled from the codebase — decisions and code drift apart over time
  - Requires a paid plan for full team history and permissions
  - No native integration with CI/CD pipelines
  - Workspace access must be managed separately from repository access

### Option 2: ADR as-code (chosen)

Store ADRs as Markdown files directly in the repository, following a lightweight
template. Tooling such as `adr-tools` or custom CI scripts can automate
numbering, status transitions, and validation.

- **More details**: Each ADR is a numbered `.md` file under `/docs/adr/`.
  A template enforces consistent structure. PRs serve as the review mechanism.
- ✅ **Advantages**:
  - Decisions live next to the code they affect — same repo, same PR, same diff
  - Full Git history: every change to a decision is versioned and attributed
  - Reviewable via standard pull request workflow the team already uses
  - Automatable: CI can enforce naming conventions, required fields, and status
  - No third-party dependency or cost
- 🚫 **Disadvantages**:
  - Requires basic Git/Markdown familiarity from all contributors
  - No rich UI — navigation is file-based unless a static site generator is added
  - Discipline required: value depends on the team consistently writing ADRs

## Decision

**We adopt ADR as-code stored in the repository under `/docs/adr/`.**

Implementation details:
- Files follow the naming convention `ADR-XXXX-short-title.md`
- Template enforced via a `ADR-template.md` at the root of the ADR directory
- Status values: `Proposed` → `Accepted` | `Rejected` | `Deprecated` | `Superseded by ADR-XXXX`
- Each ADR is submitted as a PR and requires at least one team member review before merging

## Consequences

### Positive

* Every significant decision is traceable with its date, authors, and rationale
* Onboarding new contributors is faster — they can read the ADR log to understand
  the project's history
* Evaluation presentations benefit from clear, structured justifications
* CI can automatically validate ADR format and flag missing required fields

### Negative

* Requires team discipline — ADRs only have value if written consistently
* Small overhead per decision: writing a structured ADR takes more time than a
  Slack message
* Template may feel rigid for very minor decisions (team should define a threshold
  for what warrants an ADR)

### Required Actions

1. [ ] Merge this ADR and create `/docs/adr/` directory structure
2. [ ] Add `ADR-template.md` to the repository
3. [ ] Brief team on when and how to write ADRs (one team session)
4. [ ] Add CI step to validate ADR naming and required fields
5. [ ] Write ADR-0001 for the next significant decision as a live example

## Links

* ADR concept: https://adr.github.io
* ADR Explanations: https://blog.stephane-robert.info/docs/documenter/concevoir/adr/
* adr-tools CLI: https://github.com/npryce/adr-tools
* Example ADR collection: https://github.com/joelparkerhenderson/architecture-decision-record
