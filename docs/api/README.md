# Transcendence — API Contract

Last updated: 2026-10-21

The contract is split into one file per service. The `plan/` folder holds short summaries of what we are changing and why. Each one links to the contract files that have the details.

## Reading order

1. **The plans** (the big picture, a few minutes each)
   1. [plan/01_Modification_Plan.md](plan/01_Modification_Plan.md): gateway, auth and service communication: what we implement, the solutions chosen, the order of work
   2. [plan/02_Summaries_Plan.md](plan/02_Summaries_Plan.md): where the AI summaries are stored and who reads them (enrichment pipeline)
2. **The conventions**: [00_conventions.md](00_conventions.md). They define the route kinds, the tokens, the error format and the `Status` column used in every table.
3. **How services talk to each other**: [06_service-to-service.md](06_service-to-service.md)
4. **One file per service**: read yours first, then the others as needed.

| File | What it covers |
| --- | --- |
| [00_conventions.md](00_conventions.md) | Route kinds, format, tokens, CSRF guard, errors, status codes, the `Status` column |
| [01_identity.md](01_identity.md) | Accounts, sessions (cookie), API keys, the key verification used by the gateway |
| [02_personalization.md](02_personalization.md) | Profile, topic catalog, saved articles; Frontend, Public and Internal routes; public docs page |
| [03_morning-briefing.md](03_morning-briefing.md) | The briefing; Frontend and Public routes |
| [04_content-management.md](04_content-management.md) | Articles, topics and their summaries (internal only) |
| [05_ai-processing.md](05_ai-processing.md) | The summary worker: commands, no business routes |
| [06_service-to-service.md](06_service-to-service.md) | Who calls whom with which token; summaries as an enrichment pipeline |
| [plan/01_Modification_Plan.md](plan/01_Modification_Plan.md) | Plan: gateway, auth, service-to-service calls, public API, order of work |
| [plan/02_Summaries_Plan.md](plan/02_Summaries_Plan.md) | Plan: summaries move from AI Processing to Content Management |


## Where we are

Endpoints per service, by status (see each file for the details):

| Service | Done | Partial | To do |
| --- | --- | --- | --- |
| Identity | 5 (+ `/health`) | 0 | 5 |
| Personalization | 0 (+ `/health`) | 0 | 15 |
| Morning Briefing | 0 (+ `/health`) | 0 | 3 |
| Content Management | 0 (+ `/health`) | 1 | 6 |
| AI Processing | 0 (+ `/health`) | 0 | 2 commands |
