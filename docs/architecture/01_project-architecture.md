# Project Structure Reference

## 1. Purpose

This document provides a quick reference of the repository structure.

For architectural explanations and design rules, see:

- `overview.md`
- `services.md`
- `backend-service-structure.md`
- `frontend-structure.md`

---

## 2. Repository Structure

```text
transcendence/
├── docs/                        # Project documentation
├── srcs/
│   ├── gateway/                 # API Gateway and request routing
│   ├── frontend/                # React + TypeScript application
│   └── services/                # Backend microservices
└── docker-compose.yml           # Local development environment
```

---

## 3. Backend Service Structure

Every backend service follows the same organization.

Example:

```text
services/
└── service-name/
    ├── src/
    │   ├── domain/                         # Core business rules (framework-independent)
    │   │   ├── entities/                   # Business entities
    │   │   ├── value_objects/              # Immutable domain objects
    │   │   ├── repositories/               # Repository interfaces (contracts)
    │   │   └── exceptions.py               # Domain-specific exceptions
    │   │
    │   ├── application/                    # Use cases and application services
    │   │   └── <aggregate>_application.py  # Coordinates domain objects and repositories
    │   │
    │   ├── infrastructure/                 # Technical implementations and external integrations
    │   │   ├── database/
    │   │   │   ├── models.py/              # SQLAlchemy ORM models
    │   │   │   └── repositories/           # Repository implementations using SQLAlchemy
    │   │   │
    │   │   ├── clients/                    # HTTP clients, message brokers, third-party APIs
    │   │   └── config.py                   # Configuration, settings and dependency setup
    │   │
    │   ├── api/                            # FastAPI presentation layer
    │   │   ├── routers/                    # REST endpoints
    │   │   ├── schemas/                    # Pydantic request/response models
    │   │   └── dependencies.py             # FastAPI dependency injection
    │   │
    │   ├── exceptions.py                   # Service-level exception handlers
    │   └── main.py                         # FastAPI application entrypoint
    │
    ├── tests/
    │   ├── unit/                           # Isolated business logic tests
    │   ├── integration/                    # Database/API integration tests
    │   └── e2e/                            # End-to-end service tests
    │
    ├── migrations/                         # Alembic database migrations
    ├── Dockerfile
    ├── pyproject.toml                      # Python project metadata and dependencies
    ├── uv.lock                             # Locked dependency versions
    └── README.md                           # Service documentation
```

---

## 4. Frontend Structure

The frontend follows a feature-based organization.

```text
frontend/
├── src/
│   ├── features/                     # Business features organized by domain
│   │
│   │   ├── auth/                     # Authentication and account management
│   │   │   ├── api.ts                # Gateway API calls for authentication
│   │   │   ├── components/           # Feature-specific UI components
│   │   │   ├── hooks/                # Feature-specific React hooks
│   │   │   └── types.ts              # DTOs and frontend models
│   │   │
│   │   ├── profile/                  # User profile management
│   │   ├── reading-list/             # User reading list feature
│   │   ├── articles/                 # Content browsing and management
│   │   └── briefing/                 # Morning briefing experience
│   │
│   ├── shared/                       # Reusable code shared across features
│   │   ├── components/               # Generic UI components
│   │   ├── hooks/                    # Generic reusable hooks
│   │   ├── api/                      # HTTP client and request configuration
│   │   └── utils/                    # Shared utility functions
│   │
│   ├── pages/                        # Route-level pages composed from features
│   │
│   ├── app/                          # Application bootstrap and global configuration
│   │   ├── router.tsx                # React Router configuration
│   │   ├── Layout.tsx                # Global application layout
│   │   └── providers.tsx             # Context providers (Theme, Query, Auth...)
│   │
│   └── main.tsx                      # React application entrypoint
│
├── public/                           # Static assets served as-is
├── index.html
└── package.json
```

---

## 5. Documentation Structure

```text
docs/
├── adr/
│   └── Architectural decision records
│
├── architecture/
│   ├── README.md
│   ├── overview.md
│   ├── services.md
│   ├── backend-service-structure.md
│   ├── frontend-structure.md
│   └── project-structure.md
│
├── conventions/
│   ├── commits.md
│   ├── git-workflow.md
│   └── development-principles.md
│
└── diagrams/
    └── Architecture diagrams
```

---

## 6. Quick Rules

### 6.1 Backend

Business logic:

```text
domain/
```

Use cases:

```text
application/
```

Technical implementation:

```text
infrastructure/
```

HTTP layer:

```text
api/
```

---

### 6.2 Frontend

Feature-specific code:

```text
features/
```

Reusable code:

```text
shared/
```

Route composition:

```text
pages/
```

Application setup:

```text
app/
```
