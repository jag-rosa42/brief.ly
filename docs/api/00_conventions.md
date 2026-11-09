# Conventions, authentication and errors

These rules apply to every service. The service files only list what differs. See [README.md](README.md) for the list of files.

## Conventions

### Three kinds of routes

| Kind | Path the caller uses | Path the service sees | Caller | Credential | Reached through |
| --- | --- | --- | --- | --- | --- |
| Frontend API | `https://<host>/api/<service>/<resource>` | `/<resource>` (the gateway strips `/api/<service>`) | Our React app | Access token | Traefik |
| Public API | `https://<host>/public/v1/<resource>` | `/public/v1/<resource>` (not stripped) | Third-party programs | `X-API-Key`, turned into a 60 s token by the gateway | Traefik + ForwardAuth to Identity |
| Internal API | `http://<service>:<port>/internal/v1/<resource>` | same | Other services only | Forwarded user token or service token | Direct, over the `backend` network; never routed by Traefik |

- `<service>` in a Frontend path is one of `identity`, `personalization`, `morning-briefing`.
- Any service on the gateway's network can serve Public routes, following the recipe in ADR-0009; today Personalization and Morning Briefing do. Identity has no Public route: API keys are managed only from our web app, so a leaked key can never create, list or revoke keys.
- Content Management and AI Processing are not on the gateway's network, so they only have Internal routes.
- `/internal/*`, `/health`, `/metrics` and `/docs` are never routed by the gateway.
- In each endpoint section, the heading shows the path the caller uses and `Service path` shows what the service receives.
- Every service also answers `GET /health` (container healthcheck). It is never routed, so it is listed in each service file only for completeness.

### Status column

Each service file has a `Status` column in its endpoint table. It compares the contract with the code on `main`:

| Status | Meaning |
| --- | --- |
| Done | On `main` and matches this contract |
| Partial | On `main`, but something differs or is missing; the note under the table says what |
| To do | Not on `main` yet |

### Format

| Topic | Rule |
| --- | --- |
| Format | JSON, `Content-Type: application/json`, snake_case field names |
| IDs | UUID strings, except topic IDs |
| Topic IDs | The NewsAPI category as a lowercase string, e.g. `"business"`, `"technology"` (7 topics, seeded by Content Management's migration). A topic has no separate display name: the frontend chooses the label to show for each ID. |
| Timestamps | ISO 8601 UTC, e.g. `2026-10-12T08:30:00Z` |
| Lists | Always an array, `[]` when empty, never `null` |
| `/me` routes | The account comes from the verified token (`sub`), never from the body or the path. This applies to Frontend, Public and Internal `/me` routes. |

---

## Authentication

Every token is an RS256 JWT issued by Identity (ADR-0007). Services verify it locally with Identity's public key, through `shared_auth`. The gateway never verifies JWTs.

The Public API follows the **phantom token pattern** (ADR-0009): the outside program holds an opaque API key, which means nothing on its own; on each request the gateway asks Identity to exchange it for a short-lived JWT (the public API token), and the services only ever see that JWT.

| Token | Who holds it | `aud` | `sub` | `scope` | Lifetime | Accepted on |
| --- | --- | --- | --- | --- | --- | --- |
| Access | The browser, in memory | `transcendence:api` | account id | — | 15 min | Frontend routes, and Internal routes when forwarded |
| Refresh | The browser, HttpOnly cookie | `transcendence:identity` | account id | — | 7 days | `/api/identity/auth/refresh` and `/logout` only |
| Public API | Nobody outside: created by Identity for one request, placed by the gateway | `transcendence:public-api` | key owner's account id | `read` and/or `write` | ~60 s | Public routes, and Internal routes when forwarded |
| Service | A service, cached | `transcendence:<target-service>` | `service:<name>` | route-specific | 5 min | Internal routes (issued by Identity's `POST /internal/v1/oauth/token`; no route checks them yet) |

How each route says what it accepts, in the tables below:

| Auth column | Meaning |
| --- | --- |
| None | No token |
| Bearer | `Authorization: Bearer <access token>` |
| Refresh cookie | The `refresh_token` cookie plus the header `X-Transcendence-Client: web` (CSRF guard, see below) |
| API key (`read`) | `X-API-Key: <key>` from the caller; the route needs the `read` scope |
| User (forwarded) | The token the calling service received from the user (access token or public API token), forwarded unchanged |
| Service (`<scope>`) | A service token with that scope |
| Gateway | Called only by Traefik's ForwardAuth middleware |
| Client credentials | `Authorization: Basic <client_id:client_secret>`: a backend service asking Identity for a service token |

### CSRF guard on cookie routes

The browser sends the refresh cookie automatically, even on requests started by another website. So the two routes that **read** the cookie (`/api/identity/auth/refresh` and `/logout`) also require a custom header:

```text
X-Transcendence-Client: web
```

- Without it, or with another value, Identity answers `403 CSRF_CHECK_FAILED` before reading the cookie.
- The protection comes from the header being **custom**: a cross-site form or image cannot set it, and a cross-site `fetch` with it triggers a CORS preflight that Identity refuses (`BACKEND_CORS_ORIGINS` never contains `*`). The value `web` only says which client sent it; it is not a secret.
- Defined in `srcs/services/identity/src/api/dependencies/security.py` (`ANTI_CSRF_HEADER_NAME`, `ANTI_CSRF_HEADER_VALUE`).
- Register and login only **set** the cookie, so they don't need the header.

---

## Errors

### Error body

Every error produced by a service uses this shape (`shared_errors`). `details` is only present on 422.

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request validation failed",
    "details": [
      { "field": "name", "message": "Must be 1 to 50 characters" }
    ]
  }
}
```

Some answers are produced by Traefik itself, not by a service, and **do not** use this body: `400` (encoded path), `404` (path not in the allowlist) and `429` (rate limit). Clients should rely on the status code for those.

### Status codes

| Code | When | Typical `code` |
| --- | --- | --- |
| 200 OK | Read or update succeeded | |
| 201 Created | Resource created | |
| 204 No Content | Success with no body (logout, delete) | |
| 400 Bad Request | Path with forbidden percent-encoding (gateway); service token request refused (Identity) | none (Traefik body); `UNSUPPORTED_GRANT_TYPE`, `INVALID_SCOPE` |
| 401 Unauthorized | Credential missing, invalid, expired or revoked | `INVALID_TOKEN`, `TOKEN_EXPIRED`, `TOKEN_REVOKED`, `INVALID_CREDENTIALS`, `INVALID_API_KEY`, `INVALID_CLIENT` |
| 403 Forbidden | Authenticated, but not allowed | `INSUFFICIENT_SCOPE`, `CSRF_CHECK_FAILED` |
| 404 Not Found | Resource does not exist, or path not routed (gateway) | `*_NOT_FOUND` |
| 409 Conflict | Request conflicts with current state (duplicate, limit reached) | |
| 422 Unprocessable Content | Body, path or query validation failed | `VALIDATION_ERROR` |
| 429 Too Many Requests | Rate limit hit (gateway, Public API) | none (Traefik body) |
| 500 Internal Server Error | Unexpected error | `INTERNAL_SERVER_ERROR` |
| 502 Bad Gateway | A service this one called gave an unexpected answer | `DOWNSTREAM_ERROR` |
| 503 Service Unavailable | A service this one depends on is unreachable or timed out | `SERVICE_UNAVAILABLE` |

- 422 is never used for auth errors.
- The frontend refreshes its access token only on `401` with `TOKEN_EXPIRED`. When a service gets `TOKEN_EXPIRED` from a service it called with the forwarded token, it returns `TOKEN_EXPIRED` too, so the frontend still refreshes.
- A forwarded token can expire in the middle of a chain of calls. The answer is then `401 TOKEN_EXPIRED`, and the caller (frontend or script) gets a new token and sends the whole request again. To make this rare, the frontend refreshes ahead of time when its access token has less than 60 s left, and services call the service that needs the forwarded token first (Morning Briefing asks Personalization before anything else). Calls made with a service token are not affected: the calling service renews its own service token.
