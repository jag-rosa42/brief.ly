# ADR-0006: Use a Traefik Gateway with TLS Termination and Two Container Networks

## 📋 Status

Proposed
- 📅 Date      : 06-10-2026
- 👷 Authors   : JG
- 👀 Reviewers : Transcendence Team

---

## 🧭 Context And Problem

Today every backend service publishes its own host port (8081 to 8085), the
frontend publishes 8080, and both databases publish their ports in development.
Everything shares one Compose network, and nothing speaks HTTPS.

The ft_transcendence subject requires that every connection coming from
outside the backend (browser, scripts, external API clients) uses HTTPS, while
traffic inside the backend may stay plain HTTP.

Key issues:
1. **No single entry point**: the browser would need to know every service's
   port, and every service would need its own TLS and CORS configuration.
2. **Too much exposed**: internal routes (`/health`, `/docs`, future
   `/internal/*` and `/metrics`) are reachable from the host for every service.
3. **No HTTPS**: the subject requires it for all external traffic.
4. **Unknown API paths fall through to the SPA**: the frontend's nginx answers
   `index.html` with a `200` for any unknown path, so a mistyped
   `/api/...` URL would look like a success.
5. **Rootless Podman** cannot bind ports below 1024, so `80`/`443` are not
   available.

---

## 🎯 Decision Drivers

* One HTTPS entry point for the browser, scripts and the public API
* Internal routes must be unreachable from outside, by construction
* Configuration must be readable and reviewable in git (every team member must
  be able to explain it)
* Must run with one command, with no manual certificate step
* Must work with Podman and podman-compose 1.6 (no Docker socket assumptions)
* Rate limiting and API-key delegation must be possible at the edge
  (see ADR-0009)

---

## 💡 Considered Options

### Option 1: Keep publishing each service's port

> The browser calls each service directly on its own port.

- 📝 **More details**: This is the current development setup.
- ✅ **Advantages**:
  - Nothing to build
- 🚫 **Disadvantages**:
  - No HTTPS without configuring TLS in every service
  - Internal routes are exposed
  - CORS must be configured everywhere, and cookies cannot be scoped to one origin

---

### Option 2: nginx as the gateway

> Extend an nginx container with `proxy_pass` rules, TLS and `limit_req`.

- 📝 **More details**: nginx is already used inside the frontend image.
- ✅ **Advantages**:
  - Well known, very fast
  - Already in the stack
- 🚫 **Disadvantages**:
  - Rate limiting per API key and delegated authentication (`auth_request`)
    are possible but verbose and easy to get subtly wrong
  - Mixing "serve the SPA" and "be the gateway" in one config blurs
    responsibilities

---

### Option 3: Traefik v3 configured with Docker labels

> Traefik discovers routes from labels on each Compose service.

- 📝 **More details**: The most common way Traefik is shown in tutorials.
- ✅ **Advantages**:
  - Routes live next to each service
- 🚫 **Disadvantages**:
  - Needs access to the container engine socket; with rootless Podman this
    means mounting the Podman socket into the gateway, which is a large
    privilege for an internet-facing container
  - Routing rules are scattered across Compose files and hard to review as
    a whole, which makes the allowlist (decision below) hard to audit

---

### Option 4: Traefik v3 configured with static files (file provider) ⭐ *(chosen)*

> Traefik reads its routes, middlewares and TLS settings from YAML files
> stored in the repository.

- 📝 **More details**: A static file (`traefik.yml`) declares the entry points
  and the file provider; dynamic files declare routers, middlewares and
  services. Traefik watches these files and reloads them.
- ✅ **Advantages**:
  - Built-in TLS termination, HTTP to HTTPS redirect, `StripPrefix`,
    `RateLimit` and `ForwardAuth` middlewares
  - No container socket needed
  - The whole routing table is one readable file: easy to review as an
    allowlist
- 🚫 **Disadvantages**:
  - A new tool for the team to learn
  - Adding a route means editing the gateway configuration as well as the
    service

---

## ✅ Decision

**We put a Traefik v3 gateway, configured with static files, in front of the
whole stack. It is the only container that publishes ports, it terminates
TLS, and it routes an explicit allowlist of paths over two container
networks.**

Implementation details:

- **Ports.** The gateway publishes `8080` (HTTP, which only redirects to
  HTTPS) and `8443` (HTTPS). No other container publishes a port in
  production. The application is served at `https://localhost:8443`.
  - Development works the same way: the frontend and the services are
    reached only through the gateway.
  - One development exception: the two databases and Adminer are published
    on `127.0.0.1` (this machine only), because `make test`, `make run` and
    the migration commands run on the host.
- **Configuration location.** `srcs/gateway/` (the folder already planned in
  `docs/architecture/01_project-architecture.md`).
- **Routes are an allowlist.**
  - Frontend API calls use `/api/<service>/<resource>`. The gateway removes
    the `/api/<service>` prefix before forwarding, so a service only ever sees
    its own paths (`/api/identity/auth/login` reaches Identity as
    `/auth/login`).
  - The public API uses `/public/v1/...` (see ADR-0009).
  - `/internal/*`, `/health`, `/metrics` and `/docs` are never routed.
  - The frontend router matches every path except `/api` and `/public`
    (and anything below them), so an `/api` or `/public` path that no other
    router matches gets Traefik's own `404` and never falls through to the
    frontend.
  - Paths hiding characters in percent-encoding (`%2F`, `%5C`, `%25`...) are
    refused with `400`, so an encoded `../` cannot slip past the allowlist.
  - Every other path goes to the frontend, which serves the SPA.
- **What the gateway does not do.** It does **not** validate user JWTs
  (see ADR-0007). Each service verifies tokens itself. The gateway only
  terminates TLS, routes, rate-limits, and for the public API only, delegates
  API-key checking to Identity.
- **Networks.** Two Podman networks:

  | Network | Members | Purpose |
  |---------|---------|---------|
  | `edge` | gateway, frontend, Identity, Personalization, Morning Briefing | What the gateway can reach |
  | `backend` | every backend service, `pgsql`, `pgvector` (and later Prometheus) | Service-to-service and database traffic |

  - Content Management and AI Processing are only on `backend`: the gateway
    cannot reach them at all, even by mistake.
  - `backend` is **not** `internal: true`. An internal network has no route
    to the internet, and Content Management needs NewsAPI while AI Processing
    needs an LLM API. Isolation comes from publishing no ports, not from
    cutting outbound traffic.
- **TLS certificates.**
  - If a teammate provides mkcert files, the gateway uses them (no browser
    warning once the mkcert root CA is trusted).
  - Otherwise a self-signed certificate for `localhost` is generated
    automatically at startup if none exists.
  - Certificates live in a git-ignored folder (`shared/secrets/certs/`).
    No manual step is needed to run the project.
- **Frontend nginx stays a static file server** (no TLS, no proxying, no
  security headers). Security headers belong to the gateway.

---

## 🔄 Consequences

### 🟢 Positive

* One origin (`https://localhost:8443`) for the SPA and the API: no CORS in
  production, and cookies can be scoped by path (see ADR-0007)
* Internal routes are unreachable from outside by construction, not by
  convention
* HTTPS for all external traffic, satisfying the subject
* The routing table is one file the whole team can review

### 🔴 Negative

* A new component and a new configuration language to learn
* Every new public route must be added to the gateway configuration
* Self-signed certificates show a browser warning until mkcert is used or the
  certificate is trusted manually
* Developers who used `localhost:8081`... directly must now go through the
  gateway; a service's `/docs` is browsed by running it on the host
  (`make run SERVICE=<name>`)

### 📌 Required Actions

1. [ ] Add the gateway service and its configuration in `srcs/gateway/`
2. [ ] Declare the `edge` and `backend` networks in `compose.yaml`
3. [ ] Remove published ports from every container except the gateway
   (production)
4. [ ] Add automatic certificate generation, with mkcert files taking priority
5. [ ] Review the frontend nginx configuration for behind-a-proxy issues
6. [ ] Update `docs/architecture/02_overview.md` (gateway responsibilities)

---

## 🔗 Links

* ADR-0007 — Token model and browser session
* ADR-0008 — Service-to-service authentication
* ADR-0009 — Public API
* `docs/architecture/02_overview.md`
* Traefik file provider: https://doc.traefik.io/traefik/providers/file/
* Traefik middlewares: https://doc.traefik.io/traefik/middlewares/overview/
* Podman rootless ports: https://github.com/containers/podman/blob/main/rootless.md
