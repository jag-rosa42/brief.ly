# Q
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


just focus on question 4 and 7

also i have heard about ForwardAuth concept, can it help me on my current problems? how can i implement that?



--------------------------------------------------


# A

Yes. **ForwardAuth can fit your architecture quite well**, but I would use it as an authentication _middleware at the edge_, not as a replacement for your Identity service or as a reason to build a large API Gateway.

 For Transcendence, my recommendation is:

```
                         Internet / Browser
                                |
                                | HTTPS
                                v
                         +--------------+
                         |   Traefik    |
                         | reverse proxy|
                         +--------------+
                           |     |
                    ForwardAuth  |
                           |     |
                           v     |
                    +-------------+
                    |   Identity  |
                    | /auth/check |
                    +-------------+
                           |
                    2xx = authenticated
                           |
              +------------+------------+
              |            |            |
              v            v            v
          Content   Personalization  Morning Briefing
                                           |
                                           v
                                      AI Processing
```

 This gives you a fairly clean architecture without introducing an unnecessarily complicated gateway platform.

 ## 1\. Reverse proxy vs API Gateway

 These terms overlap, which is why this can get confusing.

 ### Reverse proxy

 A reverse proxy primarily sits in front of your services and decides where requests go.

 For example:

```
/api/content/*          -> content-service
/api/personalization/*  -> personalization-service
/api/briefing/*         -> briefing-service
/api/auth/*             -> identity-service
```

 It can also handle:

 - HTTPS termination
- routing
- load balancing
- headers
- redirects
- rate limiting
- authentication middleware

 Traefik  can do these things.

 Traefik itself describes its middleware system as something attached to routers/services to modify requests, perform authentication, redirects, etc.  Traefik Docs

 ### API Gateway

 An API Gateway is essentially a reverse proxy with additional API-management responsibilities.

 Typical gateway features include:

 - authentication
- authorization
- rate limiting
- request transformation
- API versioning
- quotas
- observability
- routing
- sometimes aggregation of multiple backend calls

 You **don't need to build a custom API Gateway** for Transcendence.

 Traefik can provide the edge functionality you actually need.

 So I'd think about your architecture as:

 > **Traefik = reverse proxy + a few gateway-like middlewares**

 rather than:

 > "We need to implement an API Gateway."

---

 # 2\. Where ForwardAuth fits

 ForwardAuth is particularly interesting for your project because you already have an Identity service.

 Traefik's ForwardAuth middleware delegates authentication to an external HTTP service. If that service returns a `2xx`, Traefik allows the original request through; otherwise, it returns the authentication service's response.  Traefik Docs

 So your Identity service could expose something like:

```
GET /internal/auth/verify
```

 or:

```
GET /internal/auth/check
```

 The browser never calls this endpoint directly.

 The flow becomes:

```
Browser
   |
   | GET /api/personalization/me
   | Authorization: Bearer <access_token>
   |
   v
Traefik
   |
   | ForwardAuth
   v
Identity
   |
   | validate JWT
   |
   +---- 401/403 ---> Traefik ---> Browser
   |
   +---- 200 -------> Traefik
                         |
                         v
                 Personalization
```

 This is quite elegant for your project.

---

 # 3\. What exactly does Identity do?

 Your Identity service remains the authority responsible for authentication.

 For example:

```
POST /auth/login
       |
       v
Identity
       |
       +--> access token
       +--> refresh token
```

 Then you have an internal endpoint:

```
GET /internal/auth/check
```

 which receives:

```
Authorization: Bearer eyJ...
```

 Identity validates:

 - signature
- expiration
- issuer
- audience
- token type
- whatever other claims you require

 If valid:

```
HTTP/1.1 200 OK
```

 If invalid:

```
HTTP/1.1 401 Unauthorized
```

 Traefik then decides whether the original request should proceed.

 This means **the JWT validation logic remains associated with your Identity service**, rather than being duplicated as a complete implementation across every FastAPI service.

---

 # 4\. An important limitation of ForwardAuth

 There is one architectural distinction that is extremely important.

 ForwardAuth answers:

 > "Is this request authenticated?"

 It does **not automatically answer every authorization question**.

 For example:

```
GET /api/users/123/preferences
```

 may be authenticated, but that doesn't necessarily mean:

```
user A may access user B's preferences
```

 So I would divide responsibilities like this:

 ### Traefik / ForwardAuth

 Handles coarse-grained authentication:

```
Is there a valid authenticated user?
```

 ### Backend service

 Handles resource-level authorization:

```
Does this authenticated user have permission
to perform this operation?
```

 For example:

```
GET /users/me/preferences
```

 The Personalization service can obtain the authenticated user's identity and enforce:

```
user_id == requested_user_id
```

 or whatever authorization rules your application needs.

 This distinction prevents you from trying to turn Traefik into your entire authorization system.

---

 # 5\. How does the service know who the user is?

 This is where ForwardAuth becomes especially useful.

 Traefik supports copying headers returned by the authentication service onto the forwarded request.  Traefik Docs

 For example, Identity could return:

```
HTTP/1.1 200 OK
X-User-ID: 42
X-User-Roles: user
```

 Traefik can then forward those headers to the backend.

 So:

```
Browser
   |
   | Authorization: Bearer JWT
   v
Traefik
   |
   | Authorization
   v
Identity
   |
   | validates JWT
   |
   | X-User-ID: 42
   v
Traefik
   |
   | X-User-ID: 42
   v
Personalization
```

 Your Personalization service now knows:

```
current_user_id = 42
```

 without needing to implement the entire authentication mechanism itself.

 Traefik's current documentation explicitly supports copying selected authentication-response headers onto the forwarded request.  Traefik Docs

---

 # 6\. But don't blindly trust `X-User-ID`

 There's an important security condition here.

 You must ensure that clients cannot bypass Traefik and directly reach your backend services.

 Bad:

```
Internet
   |
   +----> Traefik ----> Personalization
   |
   +----> Personalization   <-- BAD
```

 Then an attacker could potentially send:

```
X-User-ID: 123
```

 directly to Personalization.

 Instead:

```
Internet
   |
   v
Traefik
   |
   +--> Identity
   |
   +--> Personalization
   +--> Content
   +--> Briefing
```

 and your FastAPI containers should **not publish their ports to the host**.

 Only Traefik should expose the public HTTP/HTTPS ports.

 For example conceptually:

```
services:

  traefik:
    ports:
      - "80:80"
      - "443:443"

  identity:
    # no public ports

  content:
    # no public ports

  personalization:
    # no public ports
```

 The containers communicate over the Podman network.

 That is a major part of making the `X-User-ID` pattern safe.

---

 # 7\. I would actually use two networks

 For your project, I would keep the networking fairly simple:

```
                    Public
                       |
                       v
                 +-----------+
                 |  Traefik  |
                 +-----------+
                       |
                frontend network
                       |
       +---------------+----------------+
       |               |                |
       v               v                v
   Identity        Content       Personalization
                                       |
                                       |
                                backend network
                                       |
                                       v
                                 AI Processing
```

 More concretely, you could have:

```
frontend / edge network
    |
    +-- traefik
    +-- identity
    +-- content
    +-- personalization
    +-- briefing

internal network
    |
    +-- personalization
    +-- briefing
    +-- ai-processing
    +-- databases
```

 You don't necessarily need dozens of networks.

 The important principle is:

 > **Only services that need to communicate with each other should share the relevant network.**

 And databases should not be publicly exposed.

---

 # 8\. What about the frontend?

 I'd make the frontend talk to **one origin**.

 For example:

```
https://transcendence.local/
```

 and:

```
https://transcendence.local/api/auth/...
https://transcendence.local/api/content/...
https://transcendence.local/api/personalization/...
https://transcendence.local/api/briefing/...
```

 Traefik routes these internally:

```
/api/auth/*             -> Identity
/api/content/*          -> Content
/api/personalization/*  -> Personalization
/api/briefing/*         -> Morning Briefing
```

 This is preferable to exposing:

```
identity.example.com
content.example.com
personalization.example.com
briefing.example.com
```

 unless you actually have a reason to do that.

 It also makes the frontend architecture considerably simpler.

---

 # 9\. Where does AI Processing fit?

 I would distinguish **public APIs** from **internal services**.

 For example:

```
                    Traefik
                       |
        +--------------+--------------+
        |              |              |
        v              v              v
     Content     Personalization    Briefing
                                      |
                                      |
                                      v
                                AI Processing
```

 AI Processing doesn't necessarily need to be directly accessible by the browser.

 In fact, I would make it **internal-only**.

 For example:

```
Browser
   |
   v
Traefik
   |
   v
Morning Briefing
   |
   +--> Personalization
   |
   +--> Content
   |
   +--> AI Processing
```

 That is a much cleaner boundary.

 The same applies to databases:

```
Browser
   X
Traefik
   X
AI PostgreSQL
```

 Only the appropriate backend service should reach the database.

---

 # 10\. Do you actually need ForwardAuth?

 I'd say **it is a good fit, but not mandatory**.

 You have two reasonable architectures.

 ### Option A — JWT validation in every service

```
Frontend
    |
    v
Traefik
    |
    +--> Content --------> validates JWT
    |
    +--> Personalization -> validates JWT
    |
    +--> Briefing -------> validates JWT
```

 Advantages:

 - straightforward
- services are independently secure
- no dependency on Identity for every API request

 Disadvantages:

 - JWT validation code exists in multiple services
- authorization/authentication dependencies need to be managed
- more duplicated infrastructure

 You can mitigate the duplication with a shared Python package.

---

 ### Option B — Traefik + ForwardAuth

```
Frontend
    |
    v
Traefik
    |
    v
Identity
    |
    | 200
    v
Traefik
    |
    +--> Content
    +--> Personalization
    +--> Briefing
```

 Advantages:

 - authentication is centralized at the edge
- backend APIs become simpler
- one authentication implementation
- excellent demonstration of microservice architecture
- Traefik already provides ForwardAuth

 Disadvantages:

 - backend services depend on trusted identity headers
- services must not be directly exposed
- ForwardAuth introduces a network call to Identity
- authorization still needs to be handled by the application

 For **your specific project**, I lean toward **Option B for the public API**, with some JWT/service authentication still retained internally where appropriate.

---

 # 11\. I would not make ForwardAuth handle everything

 I would structure your security boundary like this:

```
                     Browser
                        |
                    HTTPS/TLS
                        |
                        v
                 +-------------+
                 |   Traefik   |
                 +-------------+
                   |
                   | ForwardAuth
                   v
              +----------+
              | Identity |
              +----------+
                   |
             validate JWT
                   |
             +-----+-----+
             |           |
           401          200
             |           |
             X           v
                       Backend
                         |
                  authorization
                         |
                         v
                     Database
```

 The conceptual division is:

 | Responsibility | Component |
| --- | --- |
| TLS termination | Traefik |
| Public routing | Traefik |
| Authentication | Identity |
| Forward authentication check | Traefik + Identity |
| User identity propagation | Traefik headers |
| Resource authorization | Backend service |
| Business authorization | Backend service |
| Database authorization | Database/service credentials |
| Internal service authentication | Service credentials/tokens |
| Token issuance | Identity |
| Token refresh | Identity |

That is a very defensible architecture for a 42 project.

---

 # 12\. What would your Identity `/auth/check` actually do?

 Conceptually:

```
@router.get("/internal/auth/check")
async def check_auth(
    authorization: Annotated[str | None, Header()] = None,
):
    token = extract_bearer_token(authorization)

    claims = verify_access_token(token)

    return Response(
        status_code=200,
        headers={
            "X-User-ID": str(claims["sub"]),
            "X-User-Roles": ",".join(claims["roles"]),
        },
    )
```

 The important thing is that this endpoint **doesn't issue a new token**.

 It's effectively asking Identity:

 > "I received this access token. Is it valid, and who does it represent?"

 Identity responds:

```
valid -> 200
invalid -> 401
```

 Traefik then either continues or rejects the request.

---

 # 13\. Traefik configuration conceptually

 A simplified configuration would look like:

```
http:

  middlewares:

    auth:
      forwardAuth:
        address: "http://identity:8000/internal/auth/check"
        authRequestHeaders:
          - "Authorization"
        authResponseHeaders:
          - "X-User-ID"
          - "X-User-Roles"

  routers:

    personalization:
      rule: "PathPrefix(`/api/personalization`)"
      service: personalization
      middlewares:
        - auth

    content:
      rule: "PathPrefix(`/api/content`)"
      service: content
      middlewares:
        - auth

    briefing:
      rule: "PathPrefix(`/api/briefing`)"
      service: briefing
      middlewares:
        - auth
```

 The exact Traefik configuration depends on whether you're using its file provider, container labels, etc., but the architecture is the important part.

 Traefik also supports reusable middleware chains, which can be useful if several routes share the same security middleware.  Traefik Docs

---

 # 14\. What about public endpoints?

 Not everything should use ForwardAuth.

 For example:

```
POST /api/auth/login
POST /api/auth/refresh
POST /api/auth/logout
```

 must be accessible without an access token.

 So:

```
                    Traefik
                       |
            +----------+----------+
            |                     |
       public routes         protected routes
            |                     |
            v                     v
        Identity              ForwardAuth
                                  |
                                  v
                              Identity
                                  |
                                  v
                              Backend
```

 For example:

```
/api/auth/login       -> Identity
/api/auth/refresh     -> Identity
/api/auth/logout      -> Identity

/api/content/*        -> ForwardAuth -> Content
/api/personalization/*-> ForwardAuth -> Personalization
/api/briefing/*       -> ForwardAuth -> Briefing
```

---

 # 15\. What about refresh tokens?

 This is one place where I would **not involve ForwardAuth**.

 The frontend communicates with Identity:

```
Frontend
   |
   | access token expired
   v
Identity /refresh
   |
   +--> validate refresh token
   |
   +--> issue new access token
```

 ForwardAuth should simply reject an expired access token.

 The frontend then performs the refresh flow.

 So:

```
normal request
     |
     v
Traefik
     |
 ForwardAuth
     |
     +-- valid --> backend
     |
     +-- expired --> 401
                       |
                       v
                 frontend refresh
                       |
                       v
                 Identity /refresh
                       |
                       v
                 new access token
```

 That's a clean separation.

---

 # 16\. TLS

 This architecture also gives you a natural TLS termination point.

 I would do:

```
Browser
   |
   | HTTPS
   v
Traefik
   |
   | HTTP
   v
FastAPI containers
```

 for your local/42 deployment, assuming the internal Podman network is trusted and isolated.

 Traefik handles the public certificate.

 You don't need:

```
Browser
   |
 HTTPS
Traefik
   |
 HTTPS
Identity
   |
 HTTPS
Personalization
   |
 HTTPS
AI
```

 for a project running on one host/container network.

 That would add substantial certificate-management complexity without giving you much practical benefit in this environment.

 If you later distribute services across hosts or an untrusted network, then internal TLS/mTLS becomes much more interesting.

---

 # 17\. Your final architecture

 Putting everything together, I would aim for something approximately like this:

```
                         Browser
                            |
                            | HTTPS
                            |
                            v
                    +---------------+
                    |    Traefik    |
                    |               |
                    | TLS           |
                    | Routing       |
                    | ForwardAuth   |
                    +-------+-------+
                            |
                 +----------+----------+
                 |                     |
          authentication         authenticated
                 |                     |
                 v                     v
          +-------------+       +------+------+
          |  Identity   |       |             |
          |             |       |             |
          | login       |       |             |
          | refresh     |       |             |
          | JWT verify  |       |             |
          +-------------+       |             |
                                |             |
                    +-----------+-------------+-----------+
                    |           |             |           |
                    v           v             v           |
                 Content  Personalization  Briefing       |
                                               |           |
                                               v           |
                                         AI Processing     |
                                               |           |
                                               v           |
                                         AI PostgreSQL     |
                                                         |
                    Service-owned databases <-------------+
```

 But I would refine the internal part slightly:

```
                         Traefik
                            |
        +-------------------+-------------------+
        |                   |                   |
        v                   v                   v
     Content         Personalization       Briefing
                                             |
                       +---------------------+----------------+
                       |                     |                |
                       v                     v                v
                 Personalization        Content          AI Processing
                                                             |
                                                             v
                                                       pgvector DB
```

 with each service only talking to the services it actually needs.

---

 # 18\. What I would implement now

 For your 42 project, I would **not** build a custom API Gateway.

 I'd implement:

 ### 1\. Traefik

 Use it as:

 - reverse proxy
- TLS termination
- routing
- ForwardAuth
- optionally rate limiting later

 ### 2\. Identity

 Keep your existing Identity service.

 Add a small internal endpoint:

```
GET /internal/auth/check
```

 which validates the access JWT and returns the authenticated identity.

 ### 3\. Protected routes

 Configure Traefik:

```
/api/content/*
/api/personalization/*
/api/briefing/*
```

 to use ForwardAuth.

 ### 4\. Public routes

 Leave:

```
/api/auth/login
/api/auth/refresh
/api/auth/logout
```

 outside ForwardAuth.

 ### 5\. Backend services

 Don't expose their ports publicly.

 They receive trusted identity information from Traefik and perform **application-level authorization**.

 ### 6\. Internal APIs

 For:

```
Briefing -> Personalization
Briefing -> AI
Personalization -> AI
```

 don't automatically forward the browser's JWT.

 Treat these as **service-to-service calls**.

 That's a separate security boundary and is something I'd design after we examine your actual Identity implementation.

---

 ## The key idea

 I would summarize your architecture as:

 > **Identity authenticates. Traefik enforces authentication at the edge. Backend services enforce authorization.**

 And:

 > **Traefik is your reverse proxy, but you don't need to turn it into a giant API Gateway.**

 ForwardAuth is useful because it lets your existing Identity service answer the authentication question without forcing every FastAPI service to duplicate the entire JWT-validation mechanism. Traefik officially supports exactly this pattern.  Traefik Docs

 One caveat: **ForwardAuth doesn't eliminate the need for security inside your services**. It moves the coarse authentication check to the edge; your services still need to enforce permissions and protect themselves from malformed/untrusted requests.

 For Transcendence, that is a good balance between **real microservice architecture and not over-engineering a student project**.