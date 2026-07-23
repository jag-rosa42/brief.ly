# Architecture Documentation

## 1. Purpose

This directory contains the architectural documentation of the Transcendence
project.

It explains the system structure, component responsibilities, service
boundaries, and internal organization rules.

This documentation answers:

- What are the main components of the system?
- How do they communicate?
- What responsibilities belong to each service?
- Where should code be placed?

---

## 2. Documentation Map

| Document | Purpose |
|----------|---------|
| `project-architecture.md` | Quick reference of the repository structure |
| `overview.md` | High-level system architecture |
| `services.md` | Backend service responsibilities and boundaries |
| `backend-service-structure.md` | Internal organization of backend services |
| `frontend-structure.md` | Internal organization of the React application |

---

## 3. Recommended Reading Order

For new contributors, read the documents in the following order.

### 3.1 Project Structure

📄 `project-architecture.md`

Learn:

- Repository organization
- Main folders
- Backend service layout
- Frontend layout
- Documentation structure

This is the quickest way to understand where things live.

---

### 3.2 System Overview

📄 `overview.md`

Learn:

- Main components
- Communication flow
- Data ownership
- Architectural principles

---

### 3.3 Service Boundaries

📄 `services.md`

Learn:

- Service responsibilities
- Data ownership
- Service communication rules
- When to create a new service

---

### 3.4 Backend Structure

📄 `backend-service-structure.md`

Learn:

- Clean Architecture layers
- Domain/Application/Infrastructure/API responsibilities
- Where backend code belongs

---

### 3.5 Frontend Structure

📄 `frontend-structure.md`

Learn:

- Feature-based architecture
- Shared components
- Pages
- Application structure
- Where frontend code belongs

---

## 4. Architecture Principles

The project follows these main principles.

### 4.1 Backend Principles

- Clean Architecture
- Domain-driven design principles
- Separation of business logic and infrastructure
- Explicit service ownership

---

### 4.2 Frontend Principles

- Feature-based organization
- Component reuse through shared modules
- Business logic remains close to the owning feature

---

## 5. Related Documentation

### 5.1 Architectural Decisions

Location:

```text
docs/adr/
```

Contains the decisions explaining **why** architectural choices were made.

Examples:

- Why Clean Architecture was chosen
- Why Gitmoji was chosen
- Why the API Gateway pattern was adopted

---

### 5.2 Conventions

Location:

```text
docs/conventions/
```

Contains the development rules and workflows.

Examples:

- Git workflow
- Git conventions
- Commit message convention
- Development principles
