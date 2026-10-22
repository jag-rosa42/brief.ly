# ADR-0007: Adopt an RS256 Token Model and a Cookie-Based Browser Session

## 📋 Status

Proposed
- 📅 Date      : 06-10-2026
- 👷 Authors   : JG
- 👀 Reviewers : Transcendence Team

---

## 🧭 Context And Problem

The Identity service already issues RS256 JWT access and refresh tokens with
PyJWT. Refresh tokens are stored hashed, rotated on every use, and reuse of a
rotated token revokes every session of the account.

Today both tokens are returned in the JSON body, and `/auth/refresh` and
`/auth/logout` receive the refresh token in the request body. The tokens carry
`sub`, `jti`, `type`, `iat` and `exp`, but no issuer, audience or key ID.

Several services (Personalization, Morning Briefing, AI Processing, Content
Management) now need to trust these tokens.

Key issues:
1. **Token theft through XSS**: a refresh token readable by JavaScript can be
   stolen by any injected script and used for 7 to 30 days.
2. **No audience**: a token minted for one purpose (refresh, public API,
   service call) could be replayed somewhere else. Today only the `type` claim
   separates them, and only Identity checks it.
3. **No issuer or key ID**: services cannot tell who issued a token, and the
   signing key cannot be rotated without breaking every live token.
4. **CSRF**: once the refresh token is a cookie, the browser sends it
   automatically, so a malicious site could try to trigger `/refresh` or
   `/logout`.

---

## 🎯 Decision Drivers

* A stolen access token must be short-lived; the long-lived secret must not be
  readable by JavaScript
* Only Identity can create tokens; every other service can verify them alone,
  without a network call
* A token must be accepted only where it was meant to be used
* Keep the existing rotation and reuse-detection logic unchanged
* Simple enough for every team member to explain

---

## 💡 Considered Options

### Option 1: Both tokens in `localStorage`

> The SPA stores the access and refresh tokens in `localStorage`.

- 📝 **More details**: Very common in tutorials.
- ✅ **Advantages**:
  - Simple; survives page reloads
- 🚫 **Disadvantages**:
  - Any XSS can read both tokens, including the long-lived refresh token

---

### Option 2: Session entirely in cookies

> Both the access token and the refresh token are HttpOnly cookies.

- ✅ **Advantages**:
  - No token is ever visible to JavaScript
- 🚫 **Disadvantages**:
  - Every API call becomes cookie-authenticated, so every state-changing
    endpoint in every service needs CSRF protection
  - Service-to-service calls would need to turn cookies back into bearer
    tokens anyway

---

### Option 3: Access token in memory, refresh token in an HttpOnly cookie ⭐ *(chosen)*

> The SPA keeps the short-lived access token in a JavaScript variable and sends
> it as `Authorization: Bearer`. The refresh token is an HttpOnly cookie that
> the browser sends only to the auth endpoints.

- 📝 **More details**: On page load, the SPA calls `/refresh`; the cookie
  restores the session and returns a fresh access token.
- ✅ **Advantages**:
  - The long-lived secret is never readable by JavaScript
  - Ordinary API calls use bearer tokens, which browsers never send
    automatically, so they are not exposed to CSRF
  - Only two endpoints (`/refresh`, `/logout`) read the cookie and need a CSRF
    guard
- 🚫 **Disadvantages**:
  - An XSS can still use the in-memory access token while the page is open
    (limited to its 15-minute lifetime)
  - The SPA must handle refresh and retry (single-flight, see Required Actions)

---

### Signing: HS256 shared secret vs RS256 key pair

- **HS256**: every service that verifies a token holds the same secret, so
  every service could also *create* tokens. Rejected.
- **RS256** ⭐: Identity alone holds the private key; services hold only the
  public key, which can verify but never sign.

---

## ✅ Decision

**Identity is the only token issuer and the only holder of the private key.
Every token is an RS256 JWT with an issuer, an audience, a type and a key ID.
In the browser, the access token lives in memory and the refresh token in an
HttpOnly, Secure, SameSite=Strict cookie scoped to the auth endpoints.**

Implementation details:

- **Claims present in every token**: `iss`, `aud`, `sub`, `jti`, `type`,
  `iat`, `exp`, plus a `kid` header.
  - `iss` = `transcendence:identity`
  - `kid` = the RFC 7638 thumbprint of the public key, computed at startup.
    Nothing to configure; if the key changes, the `kid` changes, which
    prepares a later JWKS rotation.
  - The algorithm is pinned to RS256 when signing **and** verifying (never
    read from the token header). This blocks `alg: none` and algorithm
    confusion attacks.
- **Token kinds**:

  | Token | `type` | `aud` | `sub` | Extra | Lifetime |
  |-------|--------|-------|-------|-------|----------|
  | Access | `access` | `transcendence:api` | account ID | | 15 min |
  | Refresh | `refresh` | `transcendence:identity` | account ID | stored hashed, rotated | 7 days |
  | Public API | `access` | `transcendence:public-api` | account ID | `scope` | ~60 s (ADR-0009) |
  | Service | `service` | `transcendence:<target-service>` | `service:<name>` | `scope` | ~5 min (ADR-0008) |

  The refresh audience is accepted only by Identity, so a refresh token is
  refused everywhere else, even before its `type` is checked.
- **Browser session**:
  - Login and register return `{"access_token", "token_type"}` in the body and
    set the refresh token as a cookie:
    `refresh_token=<jwt>; HttpOnly; Secure; SameSite=Strict;
    Path=/api/identity/auth; Max-Age=<7 days>`
  - The cookie `Path` is the path **as the browser sees it**
    (`/api/identity/auth`), not as Identity sees it after the gateway removes
    the `/api/identity` prefix. Otherwise the browser would never send it.
  - `/auth/refresh` and `/auth/logout` read the cookie, not the body.
  - Both require the custom header `X-Transcendence-Client: web`
    (`ANTI_CSRF_HEADER_NAME` / `ANTI_CSRF_HEADER_VALUE` in Identity's
    `api/dependencies/security.py`). A cross-site form or image cannot set a
    custom header, and a cross-site `fetch` with one needs a CORS preflight,
    which Identity refuses for any origin not listed in
    `BACKEND_CORS_ORIGINS` (never `*`). The value only names the client; it is
    not a secret. Without the header, or with another value, they answer
    `403 CSRF_CHECK_FAILED`.
  - Refresh rotates the token and sets the new cookie.
  - Logout revokes the refresh token and deletes the cookie, and stays
    idempotent (always `204`).
- **Frontend**:
  - The access token is held in memory only (never `localStorage`).
  - On a `401` with `TOKEN_EXPIRED`, the client refreshes once and retries
    the request once. The refresh is single-flight: concurrent requests share
    one refresh call, otherwise reuse detection would revoke the session.
- **Verification** happens locally in each service through a shared package
  (ADR-0008). The gateway does not validate JWTs (ADR-0006).

---

## 🔄 Consequences

### 🟢 Positive

* A stolen access token is useful for at most 15 minutes
* The refresh token cannot be read by JavaScript
* A token cannot be replayed against a service it was not meant for
* Services verify tokens without calling Identity (no extra latency, no
  single point of failure on every request)
* Key rotation can be added later without changing the token format

### 🔴 Negative

* Revoking an access token before it expires is not possible (accepted: the
  lifetime is short; see ADR-0005)
* The cookie path ties Identity's configuration to the gateway's routing
  (`/api/identity`), so both must change together
* The `Secure` cookie requires HTTPS, so the full browser session only works
  behind the gateway (Chrome treats `http://localhost` as secure, which helps
  in development)
* Breaking change for any existing client of `/auth/refresh` and
  `/auth/logout` (only the not-yet-written frontend)

### 📌 Required Actions

1. [x] Identity: add `iss`, `aud` and `kid`; verify them; refresh lifetime 7 days
   (commit `45a861e`)
2. [x] Identity: set, rotate and clear the refresh cookie; add the CSRF header guard
   (commit `41ec9f4`)
3. [x] Identity: serve its routes without the `/api` prefix (the gateway strips it)
   (commit `903bdb0`)
4. [x] Remove the JWT keys from the migration container (commits `dcd2a30`,
   `dd7dff3`: `prestart-identity` only receives `postgres_password`)
5. [ ] Frontend: in-memory token store, single-flight refresh, session restore
   on load

---

## 🔗 Links

* ADR-0005 — Accept non-revocable access tokens
* ADR-0006 — Gateway, TLS and networks
* ADR-0008 — Service-to-service authentication
* ADR-0009 — Public API
* RFC 7519 — JSON Web Token: https://www.rfc-editor.org/rfc/rfc7519
* RFC 7638 — JWK Thumbprint: https://www.rfc-editor.org/rfc/rfc7638
* RFC 8725 — JWT Best Current Practices: https://www.rfc-editor.org/rfc/rfc8725
* OWASP CSRF Prevention (custom request headers):
  https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html
