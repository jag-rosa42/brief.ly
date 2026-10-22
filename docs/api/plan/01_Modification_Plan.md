# Next steps: gateway, auth and service communication

## 1. What we need to implement

- **A gateway (Traefik)**: the single entry point. It acts as both the *reverse proxy* (HTTPS, routing) and the *API gateway* (rate limits, API-key check).
- **Token checks in every service**, through one shared package (`shared/packages/shared_auth`).
- **Secure service-to-service calls**: no internal call without a token.
- **The Public API** (subject module): API keys, rate limiting, docs, at least 5 endpoints.
- **The user flow**: profile, saved articles, briefing, with AI summaries.

## 2. Solutions chosen

| Need | Solution |
| --- | --- |
| One entry point, HTTPS | Traefik on `https://localhost:8443`, the only container with published ports |
| Frontend → services | `/api/<service>/...`; the gateway removes `/api/<service>` before forwarding |
| Who is the user? | Identity signs JWTs; each service checks them itself with Identity's public key (`shared_auth`). The gateway does **not** check user tokens |
| Browser session | Access token in memory, refresh token in an HttpOnly cookie (**already done** in Identity) |
| Service → service | Direct calls on `/internal/v1/...`, never through the gateway. User data: forward the user's token. Other data: a *service token* from Identity |
| Public API | `/public/v1/...` with an `X-API-Key` header. The gateway rate-limits, asks Identity to check the key, and passes a 60 s token to the service (*phantom token pattern*) |
| Summaries | AI Processing writes them, Content Management stores them with the articles (*enrichment pipeline*). Nobody calls AI Processing during a request |

## 3. What changes for each of us

- **URLs**: services serve their routes **without** `/api` (Identity and Content Management already do; Personalization, Morning Briefing and AI Processing must drop it).
- **No more `localhost:8081`...**: everything goes through `https://localhost:8443`. A service's `/docs` is opened by running it on the host (`make run SERVICE=<name>`).
- **Internal routes** go under `/internal/v1/...`: never reachable from outside.
- **Topic IDs are strings** (`"business"`, `"technology"`), not UUIDs. Personalization's `profile_interest.topic_id` must change.
- **AI Processing has no routes**: a `make summarize` command reads articles from Content Management and writes the summaries back there.
- **Errors**: always the shared format `{"error": {"code", "message"}}`.

## 4. Security checks: the rules for every route

1. **Use `shared_auth`** to get the current user or service. Never decode a JWT by hand.
2. **Take the account ID from the token**, never from the URL or the body. Every query filters on it.
3. **Internal routes require a token** (a service token or a forwarded user token). Until service tokens exist, they are protected only by not being exposed: a known, temporary gap.
4. **Frontend**: keep the access token in memory (never `localStorage`); send `X-Transcendence-Client: web` on refresh and logout; on `401 TOKEN_EXPIRED`, refresh **once** and retry (shared by all pending requests).
5. **Every new public path is added to the gateway allowlist** by hand, and reviewed: an unknown path gets a 404.
6. **No secrets in code** (Podman secrets, `.env` with an `.env.example`), and **validate every input** in the frontend and the backend.

## 5. Order of work

1. `shared_auth` package (in progress)
2. Gateway, networks, HTTPS
3. Frontend: login session and token refresh
4. User flow: profile, saved articles, briefing, articles list
5. Service tokens
6. Public API and the API keys page
7. Hardening and monitoring

## 6. Needs a team decision

- **AI Processing owner**: OK to store summaries in Content Management?
- **Ingestion trigger**: a `make` command, or an HTTP route?
- **Public API rate limits**: how many requests per second?

*Details: the diagram in `docs/api/06_service-to-service.md`, and one contract file per service in `docs/api/`.*
