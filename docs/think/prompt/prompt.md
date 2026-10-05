Transcendence Project — Architecture Context & Open Questions

I am working on my final project at 42 Paris called **Transcendence**.

I want to continue an architecture discussion about the backend, authentication, networking, TLS, and communication between my microservices.

Please use the following information as context. Do **not assume that I have already made any of the architectural decisions described in the open questions below**. I want you to analyze the problem and propose appropriate solutions based on the project constraints.

## Project

The goal of Transcendence is to build a dashboard that provides personalized newspaper/news summaries to users.

For example, if a user is interested in technology, they should receive summaries of articles from approximately the last 24 hours related to technology.

Articles are retrieved using:

- NewsAPI
- newspaper3k to scrape the article content

The project contains a frontend and several backend microservices.

The frontend has already been well started.

The Identity service is almost finished.

The Content Management service is ready.

We are now starting development of:

- Personalization
- AI Processing
- other services such as Morning Briefing

Several architectural questions remain open before continuing development.

---

 ## Backend technology

 The backend is a Python microservice monorepo.

 Current technologies:

 - Python 3.14
- FastAPI
- SQLAlchemy 2+
- Alembic
- PostgreSQL
- pgvector for AI-related functionality
- Podman
- podman-compose 1.6.0

 The backend is organized as multiple independent microservices inside one monorepo.

---

## Database architecture

There are currently two PostgreSQL instances.

### PostgreSQL instance 1

Used by the AI Processing services:

- PostgreSQL
- pgvector

### PostgreSQL instance 2

Used by the other backend services.

Each service owns its own database.

Services should conceptually remain isolated from each other's databases rather than directly accessing another service's database.

---

## Current Identity service

The Identity service already exists and is almost finished.

It currently implements:

- account creation/authentication
- access tokens
- refresh tokens
- JWT
- RS256 signing

The exact implementation details will be provided separately.

I will provide the relevant Identity code later so that the architecture can be evaluated based on what already exists rather than assuming a new authentication system.

---

# Main architectural problem

The frontend will need to communicate with the backend microservices.

For example:

```
Frontend
   |
   +---- Identity
   |
   +---- Content Management
   |
   +---- Personalization
   |
   +---- Morning Briefing
   |
   +---- AI Processing
```

 Some of these APIs will be protected and require authentication/authorization.

 I need to determine how the frontend should authenticate and how authenticated requests should flow through the backend.

---

 # Question 1 — Frontend authentication and API requests

 I currently have access and refresh tokens implemented in the Identity service.

 I need to determine the correct authentication flow between the frontend and the backend.

 For example, I am wondering whether the flow should be:

```
Frontend
   |
   | login
   v
Identity Service
   |
   | access token + refresh token
   v
Frontend
   |
   | Authorization: Bearer <access_token>
   v
Protected API
```

 I need to understand:

 - How should the frontend obtain the tokens?
- Where should the access token be used?
- Where should the refresh token be used?
- Should the frontend directly call each backend service?
- Should requests go through another component first?
- How should expired access tokens be handled?
- How should refresh tokens be handled securely?
- How should logout work?
- How should protected endpoints validate the user's identity?
- How should authorization be handled in addition to authentication?

---

 # Question 2 — Communication between services

 There will be communication between backend services.

 For example:

```
Frontend
   |
   v
Personalization
   |
   v
AI Processing
```

 or:

```
Morning Briefing
   |
   +---- Personalization
   |
   +---- Content Management
   |
   +---- AI Processing
```

 I need to determine:

 - How should services authenticate each other?
- Should the user's access token be forwarded between services?
- Should services have their own credentials/tokens?
- Should service-to-service authentication be different from user authentication?
- How should a service know which user a request belongs to?
- How should authorization work for service-to-service requests?
- How can this be implemented without creating unnecessary complexity?

---

 # Question 3 — HTTPS / TLS

 The frontend will communicate with backend APIs.

 I understand that these connections should be secured using HTTPS/TLS.

 I need to determine:

 - Where should TLS terminate?
- Should every FastAPI service use HTTPS?
- Should there be a reverse proxy?
- Should certificates be handled by the reverse proxy or by each service?
- How should certificates be managed during local development?
- How should certificates be managed in a production-like deployment?
- Is HTTP acceptable for communication between backend containers?
- If internal HTTP is acceptable in some situations, what security assumptions does that require?
- When would internal HTTPS or mTLS become necessary?

 The project currently runs locally using Podman and podman-compose.

---

 # Question 4 — Reverse proxy / API Gateway

 I am considering whether I need something such as:

 - NGINX
- Traefik
- another reverse proxy
- an API Gateway
- or potentially a combination of these

 I need to understand the distinction between:

 - reverse proxy
- API Gateway
- authentication service
- identity provider
- load balancer

 I also need to determine which responsibilities should belong to each component.

 For example:

```
Frontend
    |
    v
???
    |
    +---- Identity
    +---- Content
    +---- Personalization
    +---- AI Processing
    +---- Morning Briefing
```

 I need a concrete recommendation appropriate for this project, but I want the recommendation to be based on the actual requirements rather than assuming that an API Gateway is necessary.

---

 # Question 5 — Avoiding authentication-code duplication

 One concern is that multiple FastAPI services may need to perform authentication and JWT validation.

 For example:

```
Personalization
    -> validate JWT

Content
    -> validate JWT

Morning Briefing
    -> validate JWT

AI Processing
    -> validate JWT
```

 I don't want to copy/paste the same authentication implementation into every service.

 I need to determine:

 - Should authentication be centralized?
- Should JWT validation happen in each service?
- Should an API Gateway perform authentication?
- Should there be a shared Python package/library inside the monorepo?
- Should FastAPI dependencies be shared?
- Is there an existing Python/FastAPI library that could help?
- What should be centralized and what should remain inside each service?

---

 # Question 6 — JWT / RS256 architecture

 The Identity service currently uses RS256.

 I need to determine how the other services should obtain the public key necessary to verify JWTs.

 Questions include:

 - Should the public key be copied/configured manually in every service?
- Should Identity expose a JWKS endpoint?
- Should services retrieve and cache the public key?
- How should key rotation work?
- Which JWT claims should be validated?
- Should issuer and audience be validated?
- How should access tokens and refresh tokens be distinguished?
- Should different services have different audiences/scopes?
- Should authorization use roles, scopes, permissions, or another mechanism?

---

 # Question 7 — Overall architecture

 Ultimately I need a complete architecture for:

```
                    Frontend
                       |
                       |
                       v
                Authentication
                       |
                       |
       +---------------+---------------+
       |               |               |
       v               v               v
    Content      Personalization    Morning
                                    Briefing
                       |
                       v
                 AI Processing
                       |
                       v
                  PostgreSQL
                    + pgvector
```

 The final architecture needs to answer:

 - How requests flow from the frontend to services
- How users authenticate
- How access tokens are validated
- How refresh tokens work
- How authorization works
- How services communicate
- How services authenticate each other
- Where TLS is implemented
- Where certificates are managed
- Whether a reverse proxy is needed
- Whether an API Gateway is needed
- Whether one should be built or an existing solution should be used
- How to avoid duplicated authentication code
- How Podman networking should be structured
- How the architecture can remain simple enough for a 42 project
- Which parts should be implemented now versus later

---

 # Constraints

 This is a **42 Paris final project**, so the solution should be:

 - technically sound
- secure
- understandable
- maintainable
- realistic for a student project
- compatible with FastAPI/Python
- compatible with Podman/podman-compose
- appropriate for a microservice architecture

 Avoid introducing unnecessary enterprise infrastructure unless there is a concrete reason for it.

 At the same time, don't oversimplify important security concerns.

---

 # Information I will provide next

 Before proposing the final architecture, ask me for whatever additional information you actually need.

 I can provide:

 - Identity service source code
- JWT generation code
- JWT verification code
- JWT payload examples
- FastAPI project structure
- podman-compose configuration
- Docker/Containerfiles
- current network configuration
- frontend authentication implementation
- database structure
- existing API endpoints
- any other relevant implementation details

 Once you have enough information, analyze the alternatives and propose a concrete architecture and implementation strategy.