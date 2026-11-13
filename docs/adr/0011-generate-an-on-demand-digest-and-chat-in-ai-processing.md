# ADR-0011: Generate an On-Demand Digest and Chat in AI Processing

## 📋 Status

Proposed
- 📅 Date      : 12-11-2026
- 👷 Authors   : JG
- 👀 Reviewers : Transcendence Team

---

## 🧭 Context And Problem

The subject's major module "LLM system interface" asks to generate text from
user input, handle streaming responses, and implement error handling and
rate limiting.

Today the LLM only runs in AI Processing's summary worker (ADR-0010): it
writes article and topic summaries in batch, from scraped articles, and every
user reads the same stored text. No user input reaches the LLM, nothing is
streamed to a user, and nothing needs a rate limit. ADR-0010 kept this open:
"Interactive AI features (a user asking a question) would need AI Processing
to expose a request-time route again".

Key issues:
1. **User input**: the LLM must answer what a user asks for, so it must run
   during a request, which ADR-0010 avoided for the dashboard.
2. **Cost and capacity**: one local Ollama on the host's CPU writes a few
   answers at a time, and each takes seconds. A user (or a script) asking
   again and again must not take it from everyone else.
3. **Prompt injection**: user text goes into the prompt. So do the
   summaries, which come from scraped articles.
4. **The dashboard must keep working** when the LLM is down or busy (ADR-0010).

---

## 🎯 Decision Drivers

* Meet the module's four points with a feature that fits the product (a
  personal news dashboard)
* Never make the dashboard depend on the LLM
* Protect the single LLM from overload, per user and in total
* Make prompt injection harmless, then hard
* Reuse what exists: AI Processing's Ollama client, `shared_auth`, the
  gateway's rate limiting (ADR-0009)

---

## 💡 Considered Options

### Option 1: Morning Briefing hosts the feature

> Morning Briefing already gathers the user's topics and their summaries; it
> would also call Ollama.

- ✅ **Advantages**:
  - Already on `edge`, already verifies user tokens
- 🚫 **Disadvantages**:
  - A second Ollama client, outside the AI service
  - The briefing service gains a slow, failure-prone dependency

---

### Option 2: AI Processing hosts the feature ⭐ *(chosen)*

> AI Processing serves two streaming routes, reached through the gateway.
> The summary worker is unchanged.

- 📝 **More details**: the routes read the user's topics from
  Personalization with the user's token, and the topic summaries from
  Content Management with a service token (ADR-0008), then stream the LLM's
  answer as Server-Sent Events.
- ✅ **Advantages**:
  - All LLM code stays in one service
  - Reuses the worker's Ollama stream reading and the service's client
    credentials
- 🚫 **Disadvantages**:
  - AI Processing joins the `edge` network (amends ADR-0006) and verifies
    user tokens
  - A request-time route to AI Processing, for this feature only (amends
    ADR-0010)

---

### Option 3: Call the LLM from the browser

> The frontend calls Ollama directly.

- 🚫 **Disadvantages**:
  - Exposes the LLM to the internet, with no authentication or rate limit
  - The prompt (and its rules) would be written by the client

---

## ✅ Decision

**AI Processing serves an on-demand digest and its follow-up chat, streamed
as Server-Sent Events, behind gateway rate limits; the summary pipeline of
ADR-0010 stays as it is, and no other page depends on these routes.**

Implementation details:

- **Routes** (contract: `docs/api/05_ai-processing.md`)
  - `POST /api/ai-processing/digest` (`{length, focus}`): one digest from the
    summaries of the user's topics.
  - `POST /api/ai-processing/digest/chat` (`{messages}`): answers the last
    question; the browser sends the conversation (at most 10 messages), the
    server stores nothing.
  - User access token required (`shared_auth`); the topics come from the
    token through Personalization, never from the body.
  - Answers are `text/event-stream`: `chunk` events, then `done` or `error`.
    Errors before the stream starts are ordinary JSON errors (401, 422, 503).
  - English only.
- **Data**: only the stored topic summaries, never full articles, so the
  prompt stays short. Without followed topics, or without any summary, the
  route streams a fixed message and does not call the LLM.
- **Rate limits** (gateway, `srcs/gateway/dynamic/routers.yaml`)
  - Per session (Authorization header): 6 answers a minute, burst 3.
  - In total: at most 2 answers being written at once.
  - Both answer `429` with `Retry-After`.
- **Prompt injection**
  - The model has no tools, no database, no secret and no other user's data:
    an injection can only affect the answer its own author reads.
  - A fixed system prompt; user text and summaries only in delimited blocks
    the system prompt declares as data.
  - `<`, `>` and control characters refused in typed text (422), neutralized
    in summaries and earlier answers, so no block can be closed early.
  - Answers capped in tokens; shown as plain text by the frontend.
- **Networks**: AI Processing joins `edge` (amends ADR-0006's network
  table); the gateway routes only these two paths to it.
- **Failure**: the dashboard never calls these routes; when the LLM is down,
  only the digest panel shows an error.

---

## 🔄 Consequences

### 🟢 Positive

* The module's four points are met by a feature that fits the product
* The dashboard still works without the LLM (ADR-0010 holds for it)
* One place for every LLM call
* Nothing is stored: no new table, no conversation to protect

### 🔴 Negative

* AI Processing is reachable from the gateway, for two paths
* Answers are slow on a CPU (seconds to the first words)
* Rate limits are in memory, per gateway: they reset when it restarts
* The browser sends the conversation, so it can edit earlier answers; they
  are treated as untrusted input

### 📌 Required Actions

1. [ ] AI Processing: the two routes, `shared_auth`, the Personalization and
   topic catalog clients, the streaming Ollama writer, tests
2. [ ] Gateway: the router and its two limits; compose: `edge`,
   `jwt_public_key`, `PERSONALIZATION_URL`
3. [ ] Frontend: the digest panel on the Brief page, `apiStream`
4. [ ] Contract: `docs/api/05_ai-processing.md`,
   `docs/api/06_service-to-service.md`, `docs/api/README.md`
5. [ ] Mark ADR-0006 and ADR-0010 as amended by this ADR (a line in their
   links), once accepted

---

## 🔗 Links

* ADR-0006 — Gateway and networks (amended: AI Processing on `edge`)
* ADR-0008 — Service-to-service authentication
* ADR-0009 — Public API and gateway rate limits
* ADR-0010 — Summaries as an enrichment pipeline (amended: one request-time
  feature)
* Server-Sent Events: https://html.spec.whatwg.org/multipage/server-sent-events.html
* OWASP, LLM01 Prompt Injection: https://genai.owasp.org/llmrisk/llm01-prompt-injection/
