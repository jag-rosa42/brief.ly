# Architecture Overview

## 1. Purpose

The Transcendence project is composed of a React frontend, an API Gateway,
and multiple independent backend services.

The architecture aims to provide:

- Clear separation of responsibilities.
- Independent evolution of backend capabilities.
- Strong ownership boundaries between services.
- Maintainable and testable code.

The system follows:

- Microservice architecture principles for backend services.
- Clean Architecture inside each backend service.
- Feature-based architecture inside the frontend application.

---

## 2. High-Level Architecture

```text
                         Users
                           │
                           ▼
                  React Frontend
                           │
                           ▼
                    API Gateway
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ▼                  ▼                  ▼

 Identity Service   Content Service   Personalization Service

        │                  │                  │

   Database           Database           Database
```

Each backend service owns its business logic and data.

---

## 3. Main Components

### 3.1 Frontend

Technology:

- React
- TypeScript

Responsibilities:

- User interface
- Client-side routing
- User interactions
- Feature composition
- Communication with backend through the Gateway

The frontend does not communicate directly with backend services.

---

### 3.2 API Gateway

The Gateway is the single entry point between the frontend and backend.

Responsibilities:

- Request routing
- Authentication validation
- Authorization checks
- Rate limiting (if required)
- API aggregation when needed

The Gateway hides internal service topology from the frontend.

---

### 3.3 Backend Services

Backend services represent independent business capabilities.

Each service:

- Owns its business logic.
- Owns its data.
- Exposes its API.
- Can evolve independently.

Each service follows Clean Architecture:

```text
  API
   │
   ▼
 Application
   │
   ▼
 Domain

Infrastructure
   │
   ▼
 Database / External Systems
```

---

## 4. Communication

### 4.1 Frontend → Backend

The frontend communicates only with the API Gateway.

Example:

```text
Frontend

GET /api/profile

   │
   ▼

Gateway

   │
   ▼

Personalization Service
```

---

### 4.2 Service-to-Service Communication

Services communicate through explicit interfaces.

Possible communication mechanisms:

- HTTP APIs
- Message queues
- Event-driven communication

The chosen communication method depends on the use case.

---

## 5. Data Ownership

Each service owns its database.

Example:

```text
Identity Service
        |
        ▼
 Identity Database


Content Service
        |
        ▼
 Content Database


Personalization Service
        |
        ▼
 Personalization Database
```

Services should not directly access another service's database.

If information is needed from another service:

- Use an API call.
- Use an event.
- Replicate required data when justified.

---

## 6. Architectural Principles

### 6.1 Separation of Concerns

Each component has a clear responsibility.

Examples:

- Frontend handles presentation.
- Gateway handles routing.
- Services handle business capabilities.
- Databases store service-owned data.

---

### 6.2 Domain Independence

Business rules must not depend on technical frameworks.

The domain layer should not know about:

- FastAPI
- SQLAlchemy
- PostgreSQL
- React

---

### 6.3 Explicit Ownership

Every piece of data and business logic must have a clear owner.

Avoid:

- duplicated business rules
- shared databases
- unclear responsibilities

---

## 7. Related Documentation

- `services.md`
- `backend-service-structure.md`
- `frontend-structure.md`
- ADR-0004 — Adopt Clean Architecture and Feature-Based Architecture
