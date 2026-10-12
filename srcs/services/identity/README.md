# Identity Service

## Known limitations

- **Access tokens are not revocable.** Logout and token-theft detection revoke refresh tokens
  only; an access token stays valid until it expires (`ACCESS_TOKEN_EXPIRE_MINUTES`, 15 min).
  See [ADR-0005](../../../docs/adr/0005-accept-non-revocable-access-tokens.md).
```