# Backend Service Structure

## Purpose

Every backend service follows the same directory layout.

Using a common structure makes services easier to understand, maintain, and
extend. Contributors can move from one service to another without learning a
different organization each time.

The architecture is based on **Clean Architecture**, where business logic is
kept independent from frameworks, databases, and external systems.

The goal is to ensure that:

- Business rules remain framework-independent.
- Infrastructure can evolve without impacting the domain.
- Services are easy to test.
- Responsibilities are clearly separated.

---

# Overall Structure

```text
service-name/
├── src/
│   ├── domain/
│   ├── application/
│   ├── infrastructure/
│   ├── api/
│   ├── exceptions.py
│   └── main.py
├── tests/
├── migrations/
├── Dockerfile
├── pyproject.toml
├── uv.lock
└── README.md
```

---

# Layer Responsibilities

## Domain

The **Domain** layer contains the business rules of the service.

It represents **what the business does**, independent of any technical
implementation.

The domain should be pure Python and must **not** depend on:

- FastAPI
- SQLAlchemy
- Pydantic
- HTTP
- PostgreSQL

Typical responsibilities contents include:

- Entities
- Value Objects
- Repository interfaces
- Domain exceptions
- Business rules

The domain should remain testable using only Python.

Examples:

- A user cannot challenge themselves.
- A match must contain exactly two players.
- A tournament cannot start with fewer than four participants.

---

## Application

The **Application** layer implements use cases.

It coordinates domain objects to perform business workflows.

Application services should contain very little business logic themselves.
Instead, they orchestrate interactions between domain objects and repository
interfaces.

Typical responsibilities:

- Register a new user
- Create a tournament
- Join a matchmaking queue
- Update a profile

---

## Infrastructure

Infrastructure contains every technical implementation.

This layer knows **how** data is stored or retrieved and how external systems
are accessed.

Typical responsibilities:

- SQLAlchemy models
- Repository implementations
- Database sessions
- HTTP clients
- Redis
- Configuration
- Third-party integrations

Infrastructure implements the interfaces defined by the Domain.

---

## API

The API layer exposes the service through HTTP using FastAPI.

Responsibilities include:

- Routing
- Request validation
- Response serialization
- Dependency injection
- Authentication
- Authorization
- Exception mapping

Only this layer should know that FastAPI exists.

---

# Dependency Rule

Dependencies always point toward the Domain.

```text
          HTTP Request
                │
                ▼
        FastAPI Router
                │
                ▼
      Application Service
                │
                ▼
        Domain Entities
                ▲
                │
 Infrastructure (SQLAlchemy, Redis, HTTP...)
```

The Domain never imports Infrastructure.

The Application never imports SQLAlchemy models.

Infrastructure depends on Domain interfaces—not the opposite.

---

# Directory Reference

## domain/

```text
domain/
├── entities/
├── value_objects/
├── repositories/
└── exceptions.py
```

Contains the business model.

Repository classes here are **interfaces**, not implementations.

---

## application/

```text
application/
└── <aggregate>_application.py
```

Contains use cases.

Application services coordinate repositories and domain objects.

---

## infrastructure/

```text
infrastructure/
├── database/
│   ├── models.py
│   └── repositories/
├── clients/
└── config.py
```

Contains every implementation detail.

Examples:

- SQLAlchemy repositories
- PostgreSQL models
- External API clients
- Redis clients
- Environment configuration

---

## api/

```text
api/
├── routers/
├── schemas/
└── dependencies.py
```

Contains the presentation layer.

Examples:

- FastAPI routers
- Pydantic request models
- Pydantic response models
- Dependency injection

---

# Testing Strategy

The project follows the testing pyramid.

| Layer | Test Type |
|--------|-----------|
| Domain | Unit tests |
| Application | Unit / Integration |
| Infrastructure | Integration |
| API | End-to-end |

Business logic should always be tested independently from FastAPI and the
database whenever possible.

---

# How to Decide Where Code Belongs

When adding new code, identify **what responsibility it has**, not what
technology it uses.

| If you're writing... | Put it here |
|----------------------|-------------|
| A business rule | `domain/` |
| A domain entity | `domain/entities/` |
| A value object | `domain/value_objects/` |
| A repository interface | `domain/repositories/` |
| A use case | `application/` |
| A SQLAlchemy model | `infrastructure/database/models.py` |
| A repository implementation | `infrastructure/database/repositories/` |
| A Redis client | `infrastructure/clients/` |
| An HTTP client to another service | `infrastructure/clients/` |
| A FastAPI endpoint | `api/routers/` |
| A request/response schema | `api/schemas/` |
| Dependency injection wiring | `api/dependencies.py` |
| Database configuration | `infrastructure/config.py` |

When unsure, ask yourself:

> **"Is this business logic or technical implementation?"**

If it represents a business concept, it probably belongs in the **Domain**.

If it exists because of a framework, protocol, or database, it probably belongs
in **Infrastructure** or **API**.

---

# Common Mistakes

## ❌ Putting business rules in FastAPI routers

Bad

```python
@router.post("/users")
def create_user(...):
    if len(password) < 8:
        ...
```

The password validation is a business rule and belongs in the Domain.

---

## ❌ Using SQLAlchemy models in the Domain

Bad

```python
from infrastructure.database.models import UserModel
```

The Domain should not know how data is persisted.

---

## ❌ Returning Pydantic models from the Domain

The Domain should never import Pydantic.

Pydantic belongs to the API layer.

---

## ❌ Putting SQL queries inside Application services

Database access should always be delegated to repository implementations.

---

# Design Principles

When contributing to a service, follow these principles:

- Keep business logic inside the Domain.
- Keep use cases inside the Application layer.
- Keep framework-specific code inside Infrastructure or API.
- Prefer dependency inversion over direct coupling.
- Program against interfaces, not implementations.
- Favor composition over unnecessary inheritance.
- Keep services cohesive and focused on a single business capability.

---

# Related Documentation

- ADR-0004 — Adopt Clean Architecture and Feature-Based Architecture
- `frontend-structure.md`
- `development-principles.md`
