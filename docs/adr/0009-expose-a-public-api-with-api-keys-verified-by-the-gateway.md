# ADR-0009: Expose a Public API with API Keys Verified at the Gateway

## 📋 Status

Proposed
- 📅 Date      : 06-10-2026 (updated 19-10-2026)
- 👷 Authors   : JG
- 👀 Reviewers : Transcendence Team

---

## 🧭 Context And Problem

The ft_transcendence "Public API" module requires a public API secured with
API keys, with rate limiting, documentation, and at least 5 endpoints using
`GET`, `POST`, `PUT` and `DELETE`.

Third-party programs (scripts, curl, other apps) should be able to read and
change a user's own data, which is spread over several services: the profile
and saved articles in Personalization, the daily briefing in Morning
Briefing, and possibly more later. API keys, however, are credentials, and
credentials belong to Identity (`docs/architecture/03_service.md`).

Key issues:
1. **Who owns the keys**: Identity owns credentials, but other services serve
   the data.
2. **Several services, one API**: a program should see one public API with
   one key, whatever service answers each route.
3. **Rate limiting**: must protect the stack both from one noisy IP and from
   one noisy key.
4. **One verification model**: services already verify JWTs locally
   (ADR-0008); a second, key-based verification path in each service would
   duplicate security code.
5. **Documentation**: the public docs must show only the public endpoints,
   not the internal or frontend routes.

---

## 🎯 Decision Drivers

* API keys are stored and checked only by Identity
* Every service keeps a single verification model: a JWT
* Adding public routes to a service follows the same recipe for every service
* Abuse is stopped at the edge, before reaching any service
* Keys are revocable, scoped, short-lived and never stored in clear
* The public documentation is separate from the internal API

---

## 💡 Considered Options

### Option 1: Each service checks keys by calling Identity on each request

> A service with public routes receives `X-API-Key` and calls Identity to
> validate it.

- ✅ **Advantages**:
  - No gateway logic
- 🚫 **Disadvantages**:
  - A second authentication path inside every service with public routes
  - Rate limiting per key would still need to happen somewhere

---

### Option 2: Each service owns its own API keys

> Keys are created and stored in the database of each service that has
> public routes.

- 🚫 **Disadvantages**:
  - Credentials end up outside Identity, against service ownership
  - A program needs one key per service

---

### Option 3: Gateway ForwardAuth to Identity, which returns a short-lived JWT ⭐ *(chosen)*

> For `/public/v1/*`, Traefik first rate-limits, then asks Identity whether
> the key is valid. Identity answers with a 60-second JWT that the gateway
> places in the forwarded request, whatever service receives it.

- 📝 **More details**: Traefik's `ForwardAuth` middleware sends the incoming
  request's headers to an authentication endpoint. A `2xx` lets the request
  through and can copy chosen response headers into it; any other status is
  returned to the client. This is known as the "phantom token" pattern: the
  outside world holds an opaque key, the services only ever see a JWT.
- ✅ **Advantages**:
  - Keys never leave Identity
  - Services only verify a JWT, with the shared package (ADR-0008)
  - Rate limiting and authentication happen once, at the edge, for every
    service
  - One key works on every public route
- 🚫 **Disadvantages**:
  - One extra call to Identity per public request
  - The gateway configuration becomes part of the security model and must be
    reviewed as such

---

## ✅ Decision

**Any service reachable by the gateway can expose public routes under
`/public/v1`. API keys are created, listed, revoked and verified by Identity.
On every `/public/v1` route, the gateway rate-limits per IP, then per key,
then delegates to an internal Identity endpoint through ForwardAuth, which
turns a valid key into a short-lived JWT.**

**This solution follows the phantom token pattern.** The outside program
holds an opaque credential (the API key) that carries no information and
means nothing to the services. On each request, the gateway exchanges it,
through Identity, for a short-lived JWT (the public API token), and the
services only ever see that JWT. The opaque credential can be revoked
instantly; the JWT never leaves the backend and expires within a minute.

Implementation details:

- **API keys (Identity)**
  - A logged-in user creates, lists and revokes keys from an "API keys" page
    in the frontend, which calls Identity (`/api/identity/api-keys`).
  - Identity exposes **no** public route: keys are managed only from our web
    app, so a leaked key can never create, list or revoke keys.
  - A key is a long random value with a recognizable prefix (`tr_`). It is
    shown **only once**, at creation.
  - Only its SHA-256 hash is stored. A fast hash is fine here, unlike for
    passwords, because the key is random and long, so it cannot be guessed
    from its hash.
  - Each key carries scopes: `read` and/or `write`. They mean the same thing
    on every public route, whatever service serves it.
  - A key is valid for **48 hours** after creation. An account can have at
    most **5 active keys** (not revoked and not expired).
  - Revocation is immediate: the next request with that key fails. There is
    no verification cache.
  - No "last used" date is recorded, so verification never writes to the
    database.
- **Public API token**: `type=access`, `aud=transcendence:public-api`, the
  key's scopes in `scope`, valid about 60 seconds (ADR-0007).
  - Public routes accept **only** this audience; frontend routes accept only
    `transcendence:api`. So a browser token cannot be used on the public API,
    and the reverse.
- **Gateway, the same chain for every public route** (except the
  documentation paths):
  1. Rate limit per client IP
  2. Rate limit per key (Traefik `RateLimit` keyed on the `X-API-Key` header)
  3. `ForwardAuth` to Identity's internal endpoint
     (`http://identity:8000/internal/v1/api-keys/verify`)
     - valid key: `200` with `Authorization: Bearer <token>`, which the
       gateway copies into the forwarded request
       (`authResponseHeaders: [Authorization]`), replacing anything the
       client sent
     - missing, unknown, revoked or expired key: `401`
  4. Forward the request to the service that owns the path. The path is
     **not** stripped.
- **The internal verify endpoint is never routed by the gateway.** Traefik
  calls it directly over the `edge` network, as an authentication backend,
  not as a public route.
- **Paths name resources, not services.** A program calls
  `/public/v1/me/profile`, not `/public/v1/personalization/...`. Which service
  answers is an internal detail that can change without breaking clients.
  The gateway keeps the explicit list of path prefixes per service.
- **Recipe for a service that exposes public routes:**
  1. It must be on the `edge` network (ADR-0006). Content Management and AI
     Processing are not, so they never expose public routes; their data
     reaches the public API through a service that calls them.
  2. It mounts its public router at `/public/v1`, and these routes accept
     only `aud=transcendence:public-api`.
  3. Each route declares the scope it needs (`read` or `write`) and filters
     every query by the account ID from the token.
  4. Public routes call the same use cases as the service's frontend routes;
     only the API layer differs.
  5. It serves an OpenAPI document with only its public routes, at
     `/public/v1/openapi/<service>.json`.
  6. The gateway gets one router for the service's public path prefixes,
     using the shared chain above, and the document is added to the docs
     page.
  7. If a public route calls another service on behalf of the user, it
     forwards the public API token. The internal route it calls must accept
     both `transcendence:api` and `transcendence:public-api` (ADR-0008).
- **Documentation**:
  - One Swagger UI page, `/public/v1/docs`, shows every service's public
    document with Swagger UI's document selector. One service hosts this
    page (Personalization today).
  - The docs page and the documents have their own gateway router, without
    ForwardAuth, so they are readable without a key.
  - Each service's own `/docs` stays unrouted.
- **Services with public routes today** (the contract,
  `docs/api/`, lists them in full in each service's file):

  | Service | Public routes | Scopes |
  |---------|---------------|--------|
  | Personalization | `/public/v1/topics`, `/public/v1/me/profile`, `/public/v1/me/saved-articles...` (6 routes) | `read`, `write` |
  | Morning Briefing | `/public/v1/morning-briefing` (1 route) | `read` |
  | Identity | none, by decision | — |

- **Responses**, on every public route:
  - `201` on creation, `200` on reads and updates, `204` on deletion
  - `401` without a key, or with an invalid, revoked or expired key
  - `403` when the key lacks the required scope
  - `429` when rate-limited (answered by Traefik)

---

## 🔄 Consequences

### 🟢 Positive

* Credentials stay in Identity; every service keeps one verification model
* Adding public routes to a service is a known recipe, with no new security
  code
* One key works on the whole public API
* Abuse is stopped before reaching any service
* Keys are scoped, revocable, short-lived and never stored in clear
* Public and internal APIs are clearly separated, including their docs

### 🔴 Negative

* Each public request costs one extra call to Identity (a database lookup).
  A short verification cache could be added later, at the cost of a revoked
  key working until the cache expires
* A script must get a new key every 48 hours
* Each service with public routes adds a gateway router and an OpenAPI
  document to keep in sync with the docs page
* Traefik's rate limiter is in-memory: limits reset when the gateway restarts
  and are not shared between gateway replicas (acceptable: one replica)
* The gateway configuration must be reviewed as security-critical code

### 📌 Required Actions

1. [ ] Prerequisite: service tokens (ADR-0008), so public requests never rely
   on unauthenticated internal routes
2. [ ] Identity: API key entity, table, create/list/revoke endpoints, and the
   internal verify endpoint
3. [ ] Gateway: the shared public chain (rate limits and ForwardAuth), and
   the docs router
4. [ ] Frontend: an API keys page (create, list, revoke, show once)
5. [ ] For each service with public routes (Personalization, Morning
   Briefing): apply the recipe above
6. [ ] Personalization: host the `/public/v1/docs` page

---

## 🔗 Links

* ADR-0006 — Gateway, TLS and networks
* ADR-0007 — Token model and browser session
* ADR-0008 — Service-to-service authentication
* `docs/api/README.md` — the contract, one file per service, with every public route
* Phantom token pattern (Curity): https://curity.io/resources/learn/phantom-token-pattern/
* Traefik ForwardAuth: https://doc.traefik.io/traefik/middlewares/http/forwardauth/
* Traefik RateLimit: https://doc.traefik.io/traefik/middlewares/http/ratelimit/
