# Resources

## ADR
- [Architecture Decision Records (ADR) : tracer vos choix](https://blog.stephane-robert.info/docs/documenter/concevoir/adr/)
- [Architecture Decision Record : on commence aujourd’hui](https://blog.octo.com/architecture-decision-record)

## Authentication
- [Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)
- [Password Storage Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html)
- [Ref - Security Standard - NIST SP 800-63B-4 — Authentication and Authenticator Management](https://pages.nist.gov/800-63-4/sp800-63b.html)
  **Useful sections:**
  - **§2 — Authentication Assurance Levels** → AAL1/AAL2/AAL3
  - **§3.1.1 — Passwords ⭐** → password rules & storage
  - **§3.2.2 — Rate Limiting ⭐** → protect `/auth/login` from brute force
  - **§3.2.5 — Phishing Resistance** → MFA / passkeys
  - **§5 — Session Management ⭐** → tokens, expiration, re-authentication
  - **§5.1 — Session Secrets** → JWTs / cookies

  **Read first:** §3.1.1 → §3.2.2 → §5
  **Later:** MFA, passkeys, recovery, advanced authentication



## Tokens
- [OAuth2 with Password (and hashing), Bearer with JWT tokens](https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/#hash-and-verify-the-passwords)
- [JSON Web Token (JWT)](https://datatracker.ietf.org/doc/html/rfc7519)
- [RFC 6750: The OAuth 2.0 Authorization Framework: Bearer Token Usage](https://www.rfc-editor.org/info/rfc6750/)
- [RFC 9700: BCP 240: Best Current Practice for OAuth 2.0 Security](https://www.rfc-editor.org/info/rfc9700/)

## Errors
- [Handling HTTP errors with FastAPI](https://safir.lsst.io/user-guide/fastapi-errors.html)
- [CDM MCP Server by KBaseDataLakehouse - Errors handling example - part 1](https://glama.ai/mcp/servers/KBaseDataLakehouse/datalake-mcp-server/blob/5cfb1fb4f867c42759a36f0339929674f60ccb2f/src/service/error_mapping.py)
- [CDM MCP Server by KBaseDataLakehouse - Errors handling example - part 1](https://glama.ai/mcp/servers/KBaseDataLakehouse/datalake-mcp-server/blob/5cfb1fb4f867c42759a36f0339929674f60ccb2f/src/service/errors.py)
- [Error Handling in FastAPI](https://www.geeksforgeeks.org/python/error-handling-in-fastapi/)
- [FastAPI error handling: types, methods, and best practices](https://www.honeybadger.io/blog/fastapi-error-handling/)

## FastAPI
- [I Hired a Penetration Tester to Attack My FastAPI App. He Owned Everything in 45 Minutes](https://medium.com/@rameshkannanyt0078/i-hired-a-penetration-tester-to-attack-my-fastapi-app-he-owned-everything-in-45-minutes-b66818704f6b)