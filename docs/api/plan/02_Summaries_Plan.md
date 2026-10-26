# Summaries: where they are stored and who reads them

*For: AI Processing, Content Management and Personalization.*

## 1. The issue

The first contract draft had AI Processing **create, store and serve** the summaries. That causes three problems:

- **Too many calls.** For each dashboard, Morning Briefing asks AI Processing for the summary of **every article, one by one**: about 50 internal calls for 4 topics × 10 articles. This is called the *N+1 problem*.
- **Fragile dashboard.** If AI Processing (or the LLM) is slow or down, the dashboard is slow or broken.
- **Saved articles need the summary too** (the frontend already shows it), so Personalization would also have to call AI Processing.

## 2. What we are going to do

**AI Processing computes the summaries and writes them back to Content Management. Everyone reads them from Content Management, inside the articles.**

This is a known pattern called an **enrichment pipeline**: a worker reads records from the service that owns them, adds information, and writes it back.

```
make ingest(*)   Content Management ──▶ NewsAPI          new articles, summary = null
make summarize   AI Processing ──GET articles without summary──▶ Content Management
                 AI Processing ──LLM──▶ summary
                 AI Processing ──PUT the summary──────────────▶ Content Management (stores it)

Dashboard        Morning Briefing ──▶ Content Management     articles arrive WITH their summary
Save an article  Personalization  ──▶ Content Management     article arrives WITH its summary
```

Ingestion is started manually with `make ingest`.

**Result:** at most 6 internal calls per dashboard instead of about 50, and **nobody calls AI Processing** while a user is waiting.

## 3. Impact for each service

| Service | What changes |
| --- | --- |
| **Content Management** | Stores the summaries. Articles and topics get `summary` (can be `null`) and `summarized_at`: a migration. New routes: `GET /internal/v1/articles?summary=missing`, `PUT /internal/v1/articles/{id}/summary`, `PUT /internal/v1/topics/{id}/summary`. Only AI Processing may call the `PUT`s. Still calls no other service. |
| **AI Processing** | Becomes a **worker**: no business routes (only `/health`). A `make summarize` command runs the loop, then stops. No queue, no Celery, no background loop: plain sync Python and two HTTP calls with `httpx`. The summarizer sits behind a port, so the placeholder can later become a real LLM or RAG without changing the contract. Its pgvector database keeps only its own data (embeddings, later). |
| **Personalization** | Never calls AI Processing. When a user saves an article, it gets the article from Content Management (summary included) and stores a copy. **Also:** topic IDs are strings (`"business"`), so `profile_interest.topic_id` must change from `UUID` to `String`. |
| Morning Briefing | Never calls AI Processing; gets topics and articles, with summaries, from Content Management. |

The article-summary loop reads batches of at most 25 articles, without a cursor.
It stops on an empty response or after three consecutive failures to add summaries
to Content Management; any successful write resets this global counter. This is a
provisional safety guard whose precise failure definition may change during
development.

## 4. What everyone must handle

- **`summary` can be `null`**: an article fetched since the last `make summarize` has no summary yet. The frontend hides it or shows "summary coming soon".
- **A saved article keeps the summary it had when it was saved.**
- **Only the latest topic summary** is kept.

## 5. To agree on today

1. AI Processing owner: OK to write summaries into Content Management instead of serving them?
2. Content Management owner: OK to store them and add the three routes?
3. ~~Which articles does a **topic** summary cover: the last 24 hours, or the latest N articles?~~ No chronological selection is applied.

*Details: `docs/api/04_content-management.md`, `05_ai-processing.md`, `06_service-to-service.md` (section "Summaries").*
