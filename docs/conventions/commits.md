# Commit Message Convention

## 1. Purpose

This document defines the commit message convention used by the
Transcendence team.

Commit messages are part of the project's history and should allow contributors
to quickly understand:

- What changed.
- Which area was affected.
- Why the change was introduced.

This project uses the **Gitmoji** convention to provide a consistent and
readable commit history.

The decision behind this convention is documented in:

- ADR-0003 — Commit Message Convention

---

## 2. Commit Message Format

Every commit message follows this format:

```text
<gitmoji> [<scope>] <short description>
```

Examples:

```text
✨ [auth] add JWT refresh endpoint

🐛 [gateway] fix missing authorization header

♻️ [profile] simplify avatar validation

📝 [adr] document backend architecture

✅ [identity] add unit tests for password hashing

🔧 [docker] update PostgreSQL image
```

---

## 3. Writing Guidelines

### 3.1 Keep the Description Short

A commit message should describe the change without unnecessary details.

Good:

```text
✨ [chat] add private messaging
```

Bad:

```text
✨ [chat] this commit introduces the possibility for users to privately send
messages to each other
```

---

### 3.2 Describe the Result

Commit messages should describe what the commit achieves.

Prefer:

```text
🐛 [gateway] fix JWT expiration check
```

Avoid:

```text
🐛 [gateway] fixing JWT
```

---

### 3.3 Use Imperative Mood

Commit messages should use the imperative form.

Good:

```text
✨ [user] add profile picture upload
```

Bad:

```text
✨ [user] added profile picture upload
```

---

## 4. Commit Scope

The scope identifies the main area affected by the commit.

Use the smallest meaningful scope.

Examples:

```text
auth
gateway
frontend
identity
profile
chat
game
docker
docs
adr
tests
ci
```

A scope should describe the impacted component rather than the developer's
personal task.

---

## 5. Approved Gitmoji

The following Gitmoji types are used in the project:

| Gitmoji | Meaning | Example |
|----------|---------|---------|
| ✨ | New feature | ✨ [chat] add friend invitations |
| 🐛 | Bug fix | 🐛 [gateway] fix JWT validation |
| ♻️ | Refactoring | ♻️ [game] simplify matchmaking logic |
| 📝 | Documentation | 📝 [docs] update deployment guide |
| ✅ | Tests | ✅ [identity] add repository unit tests |
| 🔧 | Tooling / configuration | 🔧 [docker] update Compose services |
| 👷 | CI/CD | 👷 [ci] add lint workflow |
| ⚡️ | Performance improvement | ⚡️ [chat] reduce database queries |

---

## 6. Good Commit Examples

```text
✨ [identity] add OAuth login

🐛 [gateway] fix token refresh race condition

♻️ [profile] extract avatar validation service

📝 [architecture] document frontend structure

✅ [chat] add websocket integration tests

🔧 [docker] add Redis container

👷 [ci] cache Python dependencies

⚡️ [game] optimize leaderboard query
```

---

## 7. Bad Commit Examples

### Too vague

```text
fix

changes

update
```

---

### Missing Scope

```text
✨ add login
```

---

### Description Too Long

```text
✨ [identity] add a new authentication system allowing users to authenticate
using OAuth providers and refresh tokens
```

---

### Incorrect Tense

```text
✨ [identity] added login endpoint
```

---

## 8. One Commit, One Purpose

Whenever practical, a commit should represent one logical change.

Good:

```text
✨ [chat] add friend invitations
```

then:

```text
✅ [chat] add unit tests for friend invitations
```

Avoid combining unrelated changes:

```text
✨ [chat] add invitations, fix tests, update Docker, improve documentation
```

Small focused commits make:

- Reviews easier.
- Reverts safer.
- Project history clearer.

---

## 9. References

- ADR-0003 — Commit Message Convention
- Gitmoji: https://gitmoji.dev
