# Identity

Identity owns accounts, tokens and API keys. Conventions, tokens and errors are in [00_conventions.md](00_conventions.md).

| Kind | Method | Caller path | Service path | Auth | Success | Status |
| --- | --- | --- | --- | --- | --- | --- |
| Frontend | POST | `/api/identity/auth/register` | `/auth/register` | None | 201 | Done |
| Frontend | POST | `/api/identity/auth/login` | `/auth/login` | None | 200 | Done |
| Frontend | POST | `/api/identity/auth/logout` | `/auth/logout` | Refresh cookie | 204 | Done |
| Frontend | POST | `/api/identity/auth/refresh` | `/auth/refresh` | Refresh cookie | 200 | Done |
| Frontend | GET | `/api/identity/accounts/me` | `/accounts/me` | Bearer | 200 | Done |
| Frontend | POST | `/api/identity/api-keys` | `/api-keys` | Bearer | 201 | To do |
| Frontend | GET | `/api/identity/api-keys` | `/api-keys` | Bearer | 200 | To do |
| Frontend | DELETE | `/api/identity/api-keys/{key_id}` | `/api-keys/{key_id}` | Bearer | 204 | To do |
| Internal | any | — | `/internal/v1/api-keys/verify` | Gateway | 200 | To do |
| Internal | POST | — | `/internal/v1/oauth/token` | Client credentials | 200 | Done |
| Internal | GET | — | `/health` | None | 200 | Done |

Where the done routes live on `main`: `srcs/services/identity/src/api/routers/auth/router.py` (auth), `srcs/services/identity/src/api/routers/accounts/router.py` (`/accounts/me`), `srcs/services/identity/src/api/routers/auth/cookie.py` (cookie), `srcs/services/identity/src/api/dependencies/security.py` (CSRF guard), `srcs/services/identity/src/api/routers/oauth/router.py` (service tokens; the client registry is `srcs/services/identity/src/infrastructure/oauth/service_clients.py`).

## Refresh cookie

Set by register, login and refresh; cleared by logout.

```text
Set-Cookie: refresh_token=<jwt>; HttpOnly; Secure; SameSite=Strict;
            Path=/api/identity/auth; Max-Age=604800
```

`Path` is the path as the browser sees it, so the browser sends the cookie only to `/api/identity/auth/...`.

## Endpoint details

Each endpoint below shows the request and every possible response.

### POST /api/identity/auth/register

Service path: `POST /auth/register`

```text
Body:
{
  "email": str,                max 255 chars
  "password": str              8-255 chars, SecretStr server-side, never logged or returned
}

201 Created           { "access_token": str, "token_type": "Bearer" } + Set-Cookie refresh_token
409 Conflict          EMAIL_ALREADY_REGISTERED
422 Unprocessable     VALIDATION_ERROR (email format, password length)
```

### POST /api/identity/auth/login

Service path: `POST /auth/login`

```text
Body:
{
  "email": str,
  "password": str
}

200 OK                { "access_token": str, "token_type": "Bearer" } + Set-Cookie refresh_token
401 Unauthorized      INVALID_CREDENTIALS
422 Unprocessable     VALIDATION_ERROR
```

### POST /api/identity/auth/logout

Service path: `POST /auth/logout`. Idempotent: always 204 once the CSRF header is present, even without a cookie or with an invalid, expired or already revoked one.

```text
Cookie: refresh_token=<jwt>
Header: X-Transcendence-Client: web
Body: none

204 No Content        refresh token revoked (if any), cookie cleared
403 Forbidden         CSRF_CHECK_FAILED (header missing or not "web")
```

### POST /api/identity/auth/refresh

Service path: `POST /auth/refresh`

```text
Cookie: refresh_token=<jwt>
Header: X-Transcendence-Client: web
Body: none

200 OK                { "access_token": str, "token_type": "Bearer" } + Set-Cookie (rotated refresh token)
401 Unauthorized      INVALID_TOKEN (missing or malformed), TOKEN_EXPIRED, TOKEN_REVOKED
403 Forbidden         CSRF_CHECK_FAILED (header missing or not "web")
```

### GET /api/identity/accounts/me

Service path: `GET /accounts/me`

```text
Header: Authorization: Bearer <access token>

200 OK
{
  "id": UUID,
  "email": str,
  "created_at": datetime
}
401 Unauthorized      INVALID_TOKEN (missing or invalid), TOKEN_EXPIRED
                      (with header WWW-Authenticate: Bearer)
```

### POST /api/identity/api-keys

Service path: `POST /api-keys`. Called by the frontend "API keys" page. The full key is returned **only here**; Identity stores only its SHA-256 hash.

A key is valid for 48 hours after creation; this cannot be changed. An account can have at most 5 active keys (not revoked and not expired).

```text
Header: Authorization: Bearer <access token>
Body:
{
  "name": str,                 1-50 chars, a label for the user ("my script")
  "scopes": ["read" | "write"] 1-2 items, no duplicates
}

201 Created
{
  "id": UUID,
  "name": str,
  "prefix": str,               first characters of the key, e.g. "tr_8f3k", to recognise it in the list
  "scopes": [str],
  "created_at": datetime,
  "expires_at": datetime,      created_at + 48 h
  "key": str                   the full key, e.g. "tr_8f3k..."; never shown again
}
401 Unauthorized
409 Conflict          API_KEY_LIMIT_REACHED (already 5 active keys)
422 Unprocessable     VALIDATION_ERROR
```

### GET /api/identity/api-keys

Service path: `GET /api-keys`. Lists the caller's active keys (not revoked and not expired), newest first.

```text
Header: Authorization: Bearer <access token>

200 OK
{
  "items": [
    {
      "id": UUID,
      "name": str,
      "prefix": str,
      "scopes": [str],
      "created_at": datetime,
      "expires_at": datetime
    }
  ]                           [] when no key
}
401 Unauthorized
```

### DELETE /api/identity/api-keys/{key_id}

Service path: `DELETE /api-keys/{key_id}`. Revocation is immediate: the next public request with that key gets 401. Idempotent.

```text
Header: Authorization: Bearer <access token>

204 No Content        revoked, or already revoked, or not one of the caller's keys
401 Unauthorized
422 Unprocessable     VALIDATION_ERROR (key_id not a UUID)
```

### POST /internal/v1/oauth/token

Gives a backend service a short-lived **service token**, with the OAuth 2.0 client credentials grant (RFC 6749 §4.4, ADR-0008). No user is involved: the token says which service is calling (`sub=service:<client_id>`), for which service (`aud`), and what it may do there (`scope`). The receiving service checks it with `shared_auth` (`require_service_scopes`). `shared_auth`'s `ClientCredentialsTokenProvider` calls this route, caches the token and renews it 30 s before it expires.

Each client authenticates with its client ID and its secret (one Compose secret per client, `<client_id with _>_client_secret`, compared in constant time). The client registry, in Identity's code, says which audience and scopes each client may get:

| Client | Audience | Scopes |
| --- | --- | --- |
| `personalization` | `transcendence:content-management` | `topics:read`, `articles:read` |
| `morning-briefing` | `transcendence:content-management` | `topics:read`, `articles:read` |
| `ai-processing` | `transcendence:content-management` | `topics:read`, `articles:read`, `summaries:write` |

```text
Header: Authorization: Basic base64(<client_id>:<client_secret>)
Header: Content-Type: application/x-www-form-urlencoded
Body (form):
  grant_type=client_credentials
  audience=transcendence:<target-service>
  scope=<scope> <scope>          space-separated, at least one

200 OK
{
  "access_token": str,          JWT: type=service, sub=service:<client_id>, aud, scope, ~5 min
  "token_type": "Bearer",
  "expires_in": int             seconds (300)
}
Headers: Cache-Control: no-store, Pragma: no-cache
401 Unauthorized      INVALID_CLIENT (no or malformed Basic header, unknown client, wrong secret;
                      same answer for all), with header WWW-Authenticate: Basic
400 Bad Request       UNSUPPORTED_GRANT_TYPE (grant_type other than client_credentials)
400 Bad Request       INVALID_SCOPE (no scope, a scope or an audience the client may not have)
422 Unprocessable     VALIDATION_ERROR (grant_type or audience missing, body not a form)
```

The errors use our shared format with the OAuth 2.0 error names in uppercase (RFC 6749 §5.2 uses `{"error": "invalid_client"}`), so every service answers errors the same way.

### /internal/v1/api-keys/verify

This route is the exchange step of the **phantom token pattern**: an opaque API key comes in, a short-lived JWT goes out. Called only by Traefik's ForwardAuth middleware, for every request on `/public/v1/*` except the docs. Traefik sends the original request's headers; Identity reads `X-API-Key`. There is no cache: every public request is one database lookup, so a revoked key fails on the very next request (a short cache is a possible future improvement, see open questions). The method Traefik uses must be checked against the Traefik docs when implementing, so the route should accept any method.

```text
Header: X-API-Key: <key>

200 OK                empty body
                      Header: Authorization: Bearer <public API token>
                        (aud=transcendence:public-api, sub=key owner, scope="read write" or subset, ~60 s)
                      Traefik copies this header into the forwarded request, replacing any
                      Authorization header the client sent.
401 Unauthorized      INVALID_API_KEY (missing, unknown, revoked or expired), returned by Traefik to the client as is
```
