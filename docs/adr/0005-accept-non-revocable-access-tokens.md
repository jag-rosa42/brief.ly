# ADR-0005: Accept Non-Revocable Access Tokens with a Short Lifetime

## 📋 Status

Accepted
- 📅 Date      : 12-10-2026
- 👷 Authors   : JG
- 👀 Reviewers : Transcendence Team

---

## 🧭 Context And Problem

The identity service issues two tokens per session:

- an **access token**: a signed JWT, valid for `ACCESS_TOKEN_EXPIRE_MINUTES` (15 min),
  verified statelessly (signature, expiry, type) on each request;
- a **refresh token**: also a JWT, but stored (hashed) in the `refresh_tokens` table, so it
  can be rotated and revoked.

Revocation only applies to refresh tokens. An access token that was issued stays valid until
it expires, even when its session ends.

Key issues:
1. **Logout**: `/auth/logout` revokes the refresh token, but the access token of that session
   keeps working for up to 15 minutes.
2. **Token theft**: when a rotated refresh token is reused, every refresh token of the account
   is revoked, but the attacker's current access token keeps working for up to 15 minutes.
3. **Other services**: services that verify access tokens locally with the public key cannot
   see any revocation state held by the identity service.

---

## 🎯 Decision Drivers

* Keep access-token verification stateless, so any service can verify a token with the public
  key, without a database lookup or a call to the identity service
* Keep the exposure window short and bounded
* Avoid new infrastructure (cache, shared denylist) at this stage of the project
* Keep the option of adding revocation later without changing the token format

---

## 💡 Considered Options

### Option 1: Short-lived, non-revocable access tokens ⭐ *(chosen)*

> Access tokens cannot be revoked; their short lifetime bounds the exposure.

- 📝 **More details**: Only refresh tokens are stored and revocable. Ending a session (logout,
  theft detection) revokes refresh tokens, so no new access token can be obtained; the current
  one expires on its own.
- ✅ **Advantages**:
  - Stateless verification in every service
  - No extra query, column or infrastructure
- 🚫 **Disadvantages**:
  - Up to `ACCESS_TOKEN_EXPIRE_MINUTES` of access after logout or theft detection

---

### Option 2: Account-level cutoff (`accounts.access_tokens_valid_after`)

> Reject access tokens whose `iat` is older than a timestamp stored on the account.

- 📝 **More details**: Set the cutoff when theft is detected (same transaction as
  `revoke_all_for_account`); `GetCurrentAccount` compares it with the token's `iat`. It costs
  no extra query, because the account is already loaded.
- ✅ **Advantages**:
  - Closes the gap where it matters most: right after theft detection
  - Also usable for "log out everywhere" or a password change
- 🚫 **Disadvantages**:
  - Doesn't cover single-device logout (a cutoff on the account would end every device)
  - Only enforced by the identity service
  - One-second precision (`iat` is whole seconds)
  - New column and migration

---

### Option 3: Session-bound access tokens

> Put a session id in the access token and check on each request that the session is active.

- ✅ **Advantages**:
  - Covers single-device logout
- 🚫 **Disadvantages**:
  - Needs a stable session id that survives refresh-token rotation (new column)
  - Adds a lookup on every authenticated request, in every service
  - Removes most of the benefit of stateless JWTs

---

### Option 4: Access-token denylist

> Store the `jti` of revoked access tokens (e.g. in Redis, with a TTL equal to their
> remaining lifetime) and reject them.

- ✅ **Advantages**:
  - Covers single-device logout
- 🚫 **Disadvantages**:
  - New infrastructure
  - Every service that verifies access tokens must query the denylist

---

## ✅ Decision

**Access tokens are short-lived and not revocable; only refresh tokens are revoked.**

Implementation details:
- `ACCESS_TOKEN_EXPIRE_MINUTES` is kept short (15 minutes)
- Logout and theft detection revoke refresh tokens only
- The frontend discards its access token on logout
- The limit is noted in `LogoutAccount`, `GetCurrentAccount` and the theft path of
  `RefreshAccountSession`

---

## 🔄 Consequences

### 🟢 Positive

* Access tokens stay verifiable by any service with the public key alone
* No additional storage, query or infrastructure

### 🔴 Negative

* After logout, the access token of the session stays valid for up to 15 minutes
* After theft detection, an attacker's access token stays valid for up to 15 minutes

### 📌 Required Actions

1. [ ] Make the frontend discard the access token on logout
2. [ ] Revisit this decision if the project adds "log out everywhere", password change or
   account deletion. Option 2 is the cheapest follow-up for these cases.
3. [ ] Consider lowering `ACCESS_TOKEN_EXPIRE_MINUTES` (5–10 min) if the window is judged too
   long

---

## 🔗 Links

* [RFC 9700: OAuth 2.0 Security Best Current Practice (refresh token rotation, token lifetime)](https://datatracker.ietf.org/doc/html/rfc9700)
* [OWASP: JSON Web Token Cheat Sheet (token revocation)](https://cheatsheetseries.owasp.org/cheatsheets/JSON_Web_Token_for_Java_Cheat_Sheet.html)