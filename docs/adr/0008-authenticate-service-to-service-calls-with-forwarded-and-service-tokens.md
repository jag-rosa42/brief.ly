# ADR-0008: Authenticate Service-to-Service Calls with Forwarded User Tokens and Service Tokens

## 📋 Status

Accepted
- 📅 Date      : 06-10-2026
- 👷 Authors   : JG
- 👀 Reviewers : Transcendence Team

---

## 🧭 Context And Problem

The briefing flow crosses several services: Morning Briefing asks
Personalization for the user's topics, then asks Content Management for the
articles and their summaries. Some work happens with no user at all: AI
Processing reads articles from Content Management, writes their summaries back
there (ADR-0010), and will embed articles ahead of time.

Each service owns its data (ADR-0004, `docs/architecture/02_overview.md`) and
must decide on its own whether a request is allowed.

Key issues:
1. **Trusting the network is not enough**: if one container is compromised,
   or a route is exposed by mistake, an unauthenticated internal API gives
   access to every user's data.
2. **Two kinds of callers**: calls made on behalf of a user, and background
   calls made by a service with no user.
3. **Duplicated security code**: five services verifying JWTs by hand would
   drift apart; one mistake (e.g. forgetting to pin the algorithm) is enough.
4. **Error propagation**: when a downstream token expires or a service is
   down, the frontend must still receive a meaningful error (`TOKEN_EXPIRED`,
   `503`), not a generic `500`.

---

## 🎯 Decision Drivers

* Every service verifies every request itself ("zero trust" inside the backend)
* No call to Identity on the hot path to validate a token
* Least privilege for background jobs (explicit scopes and audiences)
* One shared, tested implementation of verification and of the HTTP client
* Use standard mechanisms the team can look up (OAuth 2.0 client credentials)

---

## 💡 Considered Options

### Option 1: No authentication between services

> Internal routes trust any caller on the backend network.

- ✅ **Advantages**:
  - Simplest
- 🚫 **Disadvantages**:
  - A single exposed route or compromised container leaks every user's data
  - The caller must pass the user ID in the URL or body, which the callee
    must blindly trust

---

### Option 2: Static shared API keys between services

> Each service sends a fixed secret header to the others.

- ✅ **Advantages**:
  - Simple to implement
- 🚫 **Disadvantages**:
  - Long-lived secrets, no expiry, no audience, no scopes
  - Still no trustworthy user identity

---

### Option 3: Mutual TLS between services

> Each service has a certificate, and connections are mutually authenticated.

- ✅ **Advantages**:
  - Strong caller identity at the transport level
- 🚫 **Disadvantages**:
  - Requires an internal certificate authority and per-service certificates
  - Says who the calling *service* is, but not which *user* the call is for
  - The subject allows plain HTTP inside the backend; this cost buys little

---

### Option 4: Calls through the gateway

> Services call each other through Traefik, like the browser does.

- 🚫 **Disadvantages**:
  - Extra hop and TLS for no benefit
  - Would require exposing internal routes on the gateway, which ADR-0006
    forbids

---

### Option 5: Forward the user's token, or use a client-credentials service token ⭐ *(chosen)*

> On behalf of a user, forward the user's access token unchanged. Without a
> user, obtain a short-lived service token from Identity with OAuth 2.0
> client credentials. The receiving service always verifies the token with a
> shared package.

- ✅ **Advantages**:
  - The callee gets the user's identity from a signed token, never from the
    URL or body
  - Background jobs get narrow, short-lived rights (audience + scopes)
  - Verification is local and identical in every service
- 🚫 **Disadvantages**:
  - A forwarded user token can expire mid-chain (handled by error mapping)
  - One more secret per background client

---

## ✅ Decision

**Services call each other directly by container name, over HTTP, on
`/internal/...` routes, and always authenticate with a JWT that the receiving
service verifies locally with a shared package. On behalf of a user, the
caller forwards the user's token unchanged; without a user, it uses a service
token from Identity obtained with OAuth 2.0 client credentials.**

Implementation details:

- **Shared package** `shared/packages/shared_auth`, packaged and wired like
  `shared_errors` (uv path source, `additional_contexts`, development volume
  mount). It provides:
  - **A token verifier**, built once at application startup (so a bad
    configuration fails immediately, not on the first request). It checks:
    - the RS256 signature with Identity's public key (a Podman secret)
    - the algorithm, pinned to RS256
    - the issuer
    - the audiences this service accepts
    - the required claims
    - the token type
    Refresh tokens are always rejected.
  - **FastAPI dependencies**:
    - current user (a browser access token)
    - forwarded user (a user token forwarded by another service: access
      token or public API token)
    - current service
    - required scopes, for a service token or a public API token
    No route accepts both a user and a service: see "Which token for which
    call" below.
  - **A test helper** that signs tokens with a test key, so services test
    their routes through the real checks.
  - **An HTTP client** for internal calls:
    - forwards the token
    - applies a timeout
    - maps errors: a downstream `TOKEN_EXPIRED` reaches the frontend as
      `TOKEN_EXPIRED`; a dead or timed-out service becomes `503`
  - **A service-token provider**: requests a token from Identity, caches it,
    and renews it shortly before it expires.
- **Which token for which call**: the choice depends on **whose data** the
  callee holds, not on whether a user started the request.
  - The callee holds **this user's** data (e.g. Morning Briefing →
    Personalization for the profile): forward the user's token.
  - The callee holds data that belongs to **no user** (Content Management's
    articles, topics and summaries): use the caller's own service token, even
    while handling a user's request. Content Management therefore only ever
    accepts service tokens.
- **On behalf of a user**: forward the incoming `Authorization: Bearer`
  header unchanged. Use cases never see tokens: the API layer builds the HTTP
  adapters per request with the token.
  - The forwarded token is either the user's access token
    (`aud=transcendence:api`, the request came from our frontend) or a
    public API token (`aud=transcendence:public-api`, the request came from
    a script through the Public API, ADR-0009). An internal route that
    accepts forwarded tokens accepts both audiences; the scope was already
    checked by the route that received the public request.
  - A forwarded token can expire in the middle of the chain. The downstream
    service answers `401 TOKEN_EXPIRED`, the caller passes it through, and
    the client gets a new token and resends the whole request. To keep this
    rare: the frontend refreshes when its token has less than 60 s left, and
    a service makes its forwarded-token calls first, before slower work done
    with its service token.
- **Without a user**:
  - The service calls Identity's `/internal/v1/oauth/token` with
    `grant_type=client_credentials`, its client ID, and a secret stored as a
    Podman secret.
  - It receives a token with `type=service`, `sub=service:<name>`,
    `aud=transcendence:<target-service>` and a `scope` claim, valid about
    5 minutes.
- **Client registry**: which client may request which audience and scopes is
  declared in a configuration file inside Identity that contains **no
  secret**. Each client secret is one Podman secret, mounted into the calling
  service and into Identity (which compares it in constant time). The exact
  storage is settled in the phase that implements it.
- **Authorization** is ownership-based: every query filters by the account ID
  taken from the verified token, never from the URL or body. Service tokens
  must also carry the scope the route requires. There are no user roles yet.

---

## 🔄 Consequences

### 🟢 Positive

* A compromised container or exposed route does not grant access to other
  users' data without a valid token
* Background jobs have least privilege and short-lived credentials
* JWT verification is written and tested once
* Error semantics stay consistent across the chain

### 🔴 Negative

* Every service gains a dependency on the shared package and on Identity's
  public key
* A user token may expire during a long chain; the client must refresh and
  resend the whole request (ADR-0007), so the work done so far is lost
* One more secret to generate per background client
* Identity is on the path to obtain service tokens (mitigated by caching)

### 📌 Required Actions

1. [x] Create `shared/packages/shared_auth` with its tests
2. [ ] Wire it into every service (pyproject, Dockerfiles, compose contexts,
   development mounts). Done: Personalization, Morning Briefing. Left:
   Content Management, AI Processing
3. [x] Add Identity's client-credentials endpoint and the client registry file.
   Service tokens are built **before** the Public API (ADR-0009), so no
   public request ever relies on unauthenticated internal routes.
   Until then, internal routes are unauthenticated (known gap).
4. [x] Add a secret in `shared/mk/secrets.mk` for each client that needs service
   tokens: AI Processing, Morning Briefing, Personalization
5. [ ] Add `/internal/...` routes in the services that need them

---

## 🔗 Links

* ADR-0006 — Gateway, TLS and networks
* ADR-0007 — Token model and browser session
* ADR-0009 — Public API
* ADR-0010 — Summaries stored in Content Management (enrichment pipeline)
* RFC 6749 §4.4 — OAuth 2.0 Client Credentials Grant:
  https://www.rfc-editor.org/rfc/rfc6749#section-4.4
* RFC 8725 — JWT Best Current Practices: https://www.rfc-editor.org/rfc/rfc8725
