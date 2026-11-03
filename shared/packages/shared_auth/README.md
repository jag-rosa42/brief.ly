# Shared Authentication Package

Token verification and service-to-service calls for the backend services
(ADR-0007 tokens, ADR-0008 service-to-service, ADR-0009 public API).

- Tokens are verified locally with Identity's public key: no call to Identity.
- Routes get the caller (user or service) through FastAPI dependencies.
- Other services are called with a forwarded user token or a service token.

## Install in a service

Same wiring as `shared_errors` (pyproject `[tool.uv.sources]`, Dockerfile
`COPY --from`, compose `additional_contexts` and dev volume). `shared_auth`
depends on `shared_errors`, so the service needs both.

```toml
dependencies = ["shared-auth", "shared-errors"]

[tool.uv.sources]
shared-auth = { path = "../../../shared/packages/shared_auth", editable = true }
shared-errors = { path = "../../../shared/packages/shared_errors", editable = true }
```

`editable = true` is required on both: `shared_auth` declares `shared-errors`
as editable, and uv refuses two different sources for one package.

The service also needs the `jwt_public_key` secret in `compose.yaml`, and
`generate-jwt-keys: true` for its CI job (the app loads the key at startup).

## Set up at startup

```python
from shared_auth import AuthSettings, install_authentication
from shared_errors import register_shared_exception_handlers

auth_settings = AuthSettings(_env_file=BASE_DIR / ".env", _secrets_dir=SECRETS_DIR)

app = FastAPI()
register_shared_exception_handlers(app)
install_authentication(app, auth_settings)  # fails here if the key is invalid
# A service that accepts public API tokens (ADR-0009):
# install_authentication(app, auth_settings, public_api=True)
```

| Setting | Required | Default |
| --- | --- | --- |
| `JWT_PUBLIC_KEY` | yes (the `jwt_public_key` secret) | |
| `JWT_SERVICE_AUDIENCE` | yes, e.g. `transcendence:personalization` | |
| `JWT_ISSUER` | no | `transcendence:identity` |
| `JWT_ACCESS_AUDIENCE` | no | `transcendence:api` |
| `JWT_PUBLIC_API_AUDIENCE` | with `public_api=True` (checked at startup) | `None` |

## Protect routes

| Dependency | Accepts |
| --- | --- |
| `CurrentUserDep` | browser access token |
| `CurrentForwardedUserDep` | user token forwarded by another service (browser or public API) |
| `CurrentServiceDep` | service token addressed to this service |
| `Depends(require_service_scopes("x:write"))` | service token holding the scopes |
| `Depends(require_public_api_scopes("write"))` | public API token holding the scopes |

```python
@router.get("/me/profile")
def get_profile(user: CurrentUserDep): ...  # user.account_id, user.token


SummaryWriter = Annotated[
    ServicePrincipal, Depends(require_service_scopes("summaries:write"))
]


@router.put("/internal/v1/articles/{article_id}/summary")
def put_summary(service: SummaryWriter): ...  # service.name, service.scopes
```

Always filter data by `user.account_id`, never by an ID from the URL or body.

## Call another service

```python
personalization = DownstreamClient("personalization", "http://personalization:8000")

# On behalf of a user: forward their token unchanged.
profile = personalization.get_json("/internal/v1/me/profile", token=user.token)

# Without a user: a service token (OAuth 2.0 client credentials), cached and renewed.
content = DownstreamClient("content-management", "http://content-management:8000")
tokens = ClientCredentialsTokenProvider(
    issuer_service="identity",
    token_endpoint_url="http://identity:8000/internal/v1/oauth/token",
    client_id="ai-processing",
    client_secret=settings.CLIENT_SECRET,  # SecretStr, from a Compose secret
    audience="transcendence:content-management",
    scopes=["articles:read"],
)
content.get_json("/internal/v1/articles", token=tokens.get_token())
```

Create both once at startup and `close()` them on shutdown.

## Errors

All answers use the `shared_errors` format.

| Situation | Status | `error.code` |
| --- | --- | --- |
| no token, bad token, wrong kind of token | 401 | `INVALID_TOKEN` |
| expired token (here or downstream) | 401 | `TOKEN_EXPIRED` |
| missing scope | 403 | `INSUFFICIENT_SCOPE` |
| downstream service down, timed out, or 502/503/504 | 503 | `SERVICE_UNAVAILABLE` |
| other downstream error | 502 | `DOWNSTREAM_ERROR` |

An adapter can catch `DownstreamError` (e.g. to turn a downstream 404 into its own error).

## Test your routes

`FakeTokenIssuer` plays Identity: it signs real tokens with a test key, and
the app verifies them through the real checks.

```python
from shared_auth.testing import FakeTokenIssuer

issuer = FakeTokenIssuer()  # one per test session: key generation is slow
issuer.override_authenticator(app, service_audience="transcendence:personalization")

client.get("/me/profile", headers=issuer.bearer(issuer.user_token(account_id)))
issuer.user_token(account_id, expires_in=timedelta(seconds=-1))  # expired
issuer.service_token("ai-processing", audience="transcendence:content-management", scopes=["articles:read"])
issuer.public_api_token(account_id, scopes=["read"])  # needs public_api=True
```

Clear `app.dependency_overrides` after each test.

## Package tests

```bash
uv run pytest
```
