# ADR-0010: Store AI Summaries in Content Management as an Enrichment Pipeline

## 📋 Status

Accepted
- 📅 Date      : 19-10-2026
- 👷 Authors   : JG
- 👀 Reviewers : Transcendence Team

---

## 🧭 Context And Problem

AI Processing writes summaries of articles and topics with an LLM. Three
consumers need them: Morning Briefing (the dashboard), Personalization (the
saved articles, whose snapshot must include the summary, as the frontend
already expects), and through them the frontend and the Public API.

The earlier contract draft had AI Processing both write and serve the
summaries. Morning Briefing then called AI Processing once per article and
once per topic on every dashboard load, and Personalization would have had to
call it on every save.

Key issues:
1. **Where summaries live**: in the service that writes them, or next to the
   articles they describe.
2. **Request-time dependencies**: every service called during a dashboard
   request is one more way for the dashboard to fail or slow down.
3. **Load**: one call per article on every dashboard load does not scale.
4. **Future AI work**: AI Processing should be free to change how it
   summarizes (another model, RAG over embeddings) without breaking others.

---

## 🎯 Decision Drivers

* The dashboard must not depend on the LLM, or on AI Processing, at request time
* A summary is computed once and read everywhere
* As few internal calls as possible per dashboard load
* AI Processing's internals can change without changing the contract

---

## 💡 Considered Options

### Option 1: AI Processing stores and serves summaries; Personalization copies one at save time

> Readers call AI Processing for summaries; Personalization calls it when an
> article is saved.

- ✅ **Advantages**:
  - Summaries stay where they are produced
- 🚫 **Disadvantages**:
  - Morning Briefing depends on AI Processing on every request, one call per
    article (or a batch route to add)
  - Personalization gains a dependency on AI Processing

---

### Option 2: Readers ask AI Processing every time they read

> Nobody stores a copy; Personalization asks AI Processing each time saved
> articles are listed.

- ✅ **Advantages**:
  - Always the latest summary
- 🚫 **Disadvantages**:
  - The most-used reads depend on the slowest service; listing saved articles
    fails when AI Processing is down

---

### Option 3: AI Processing writes summaries back to Content Management ⭐ *(chosen)*

> AI Processing is a worker: it reads articles from Content Management,
> computes summaries, and stores them in Content Management. Everyone reads
> summaries from Content Management, inside the article and topic objects.

- 📝 **More details**: this is the **enrichment pipeline** pattern. A worker
  reads records from their system of record, computes extra information, and
  writes it back; readers only talk to the system of record. A related name
  is the **Content Enricher** pattern from *Enterprise Integration Patterns*
  (Hohpe and Woolf).
- ✅ **Advantages**:
  - No service calls AI Processing during a request
  - Articles and their summaries arrive in one call
  - AI Processing's internals can change freely
- 🚫 **Disadvantages**:
  - Content Management stores data it does not produce
  - Summaries exist only after a run

---

## ✅ Decision

**Summaries follow the enrichment pipeline pattern: AI Processing computes
them and writes them back to Content Management, which stores them with the
articles and topics. Every other service reads summaries from Content
Management and never calls AI Processing.**

Implementation details:

- **Content Management (system of record)**
  - Article summaries are stored in a dedicated one-to-zero-or-one
    `article_summaries` table. The absence of a row represents a missing
    summary. The row stores the text, generation timestamp, model, quality
    decision and comment, and generation duration in milliseconds. Topic
    summaries are stored similarly in a dedicated `topic_summaries` table,
    with the common text, timestamp, and model fields. The model is stored for
    traceability only.
    A summary is written in its article's language, which the article already
    stores (`language`), so no summary language is kept.
  - Content Management derives the non-persisted `read_time_minutes` from the
    stored article summary, rounded up at 200 words per minute. It returns `0`
    when no summary exists. AI Processing does not calculate or send this value.
  - New routes: `GET /internal/v1/articles?summary=missing`,
    `PUT /internal/v1/articles/{article_id}/summary`,
    `PUT /internal/v1/topics/{topic_id}/summary`.
  - The `PUT` routes require a service token with `summaries:write`, which
    only AI Processing's client may obtain (ADR-0008).
  - Only the latest topic summary is kept.
- **AI Processing (worker)**
  - No business routes: only `/health` (and `/metrics` later).
  - A `summarize` command, run by hand inside its container (for example
    `make summarize`), loops: fetch articles without a summary, summarize
    each with the LLM, `PUT` the result; then summarize each topic from its
    articles.
  - It uses the existing sync SQLAlchemy setup; the job is sequential. A
    thread pool can be added if a run becomes too slow.
  - Its pgvector database holds only its own working data (embeddings, for
    grouping similar articles and for RAG later), never summaries.
  - The summarizer stays behind a port (`application/`), so a RAG-based
    summarizer is a new adapter, not a new contract.
- **Readers**
  - Morning Briefing gets topics and articles, summaries included, from
    Content Management with its service token.
  - Personalization copies the article's summary into the saved-article
    snapshot when an article is saved.
  - A missing summary is `null`; the frontend must handle it.

---

## 🔄 Consequences

### 🟢 Positive

* The dashboard keeps working when AI Processing or the LLM is down
* Each summary is computed once and read by every service from one place
* A dashboard load makes at most 6 internal calls (1 profile, 1 topic list,
  1 article list per interest, max 4), instead of about 50 (one summary call
  per article and per topic to AI Processing)
* Content Management still calls no other service; Morning Briefing and
  Personalization no longer depend on AI Processing
* AI Processing can change models or add RAG without changing the contract

### 🔴 Negative

* Articles ingested since the last run have no summary until the next run
* Content Management needs a migration and two write routes for data it does
  not produce
* No history of topic summaries
* A saved article keeps the summary it had when saved
* Summaries cannot be requested on demand
* Interactive AI features (a user asking a question) would need AI Processing
  to expose a request-time route again

### 📌 Required Actions

1. [ ] Content Management: summary columns (migration), the `summary=missing`
   filter, the two `PUT .../summary` routes
2. [ ] AI Processing: the `summarize` command, with the summarizer behind a
   port, and a `make summarize` target
3. [ ] Morning Briefing: read summaries from Content Management; no client
   for AI Processing
4. [ ] Personalization: copy the summary into the saved-article snapshot
5. [ ] Frontend: handle `summary: null`
6. [ ] Update `docs/architecture/03_service.md`: Content Management owns
   articles and topics **with their summaries**; AI Processing owns its
   processing workflows and embeddings; Morning Briefing no longer depends on
   AI Processing

---

## 🔗 Links

* ADR-0004 — Clean architecture for backend services
* ADR-0008 — Service-to-service authentication
* `docs/api/06_service-to-service.md` — section "Summaries: an enrichment pipeline"
* Enterprise Integration Patterns, Content Enricher:
  https://www.enterpriseintegrationpatterns.com/patterns/messaging/DataEnricher.html
