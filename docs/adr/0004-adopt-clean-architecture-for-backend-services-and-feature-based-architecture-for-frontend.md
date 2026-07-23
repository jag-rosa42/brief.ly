# ADR-0004: Adopt Clean Architecture for Backend Services and Feature-Based Architecture for the Frontend

## 📋 Status

Accepted
- 📅 Date      : 24-07-2026
- 👷 Authors   : JG
- 👀 Reviewers : Transcendence Team

---

## 🧭 Context And Problem

The Transcendence project is expected to grow into multiple backend services and
a React frontend developed collaboratively.

Without a shared architectural structure, contributors are likely to organize
code according to personal preferences, resulting in:

1. **Inconsistent project layouts** across services
2. **Business logic coupled to frameworks** (FastAPI, SQLAlchemy, React)
3. **Poor separation of concerns**, making testing and maintenance harder
4. **Difficult onboarding**, as every service or feature would require learning
   a different organization

To ensure long-term maintainability, every service and frontend feature should
follow the same architectural principles.

---

## 🎯 Decision Drivers

* Consistent project structure across all services
* Clear separation of business logic and infrastructure
* Framework-independent domain logic
* High testability
* Easy onboarding of new contributors
* Scalability as additional services and frontend features are introduced

---

## 💡 Considered Options

### Option 1: Layered (MVC-style) Architecture

> Organize projects by technical layers such as controllers, services,
> repositories and models.

- 📝 **More details**:
  Business logic is often implemented inside service classes while controllers
  orchestrate requests and repositories access the database.

- ✅ **Advantages**
  - Familiar to most developers
  - Simple for small projects
  - Minimal abstraction

- 🚫 **Disadvantages**
  - Business logic often becomes coupled to framework code
  - Boundaries between layers tend to blur over time
  - Difficult to keep domain logic independent

---

### Option 2: Technology-Oriented Organization

> Organize the repository by framework or library.

Example:

```
controllers/
models/
schemas/
database/
```

- 📝 **More details**
  Files are grouped according to the framework component they belong to.

- ✅ **Advantages**
  - Easy to understand initially
  - Common in tutorials

- 🚫 **Disadvantages**
  - Features become scattered across many folders
  - Difficult to identify ownership
  - Poor scalability as the project grows

---

### Option 3: Clean Architecture (Backend) + Feature-Based Architecture (Frontend) ⭐

> Separate business rules from technical concerns while organizing frontend
> code around business features rather than file types.

- 📝 **More details**

  Backend services follow four primary layers:

  - Domain
  - Application
  - Infrastructure
  - API

  Frontend code is organized into feature modules that encapsulate their own
  components, hooks, API calls and types.

- ✅ **Advantages**
  - Strong separation of concerns
  - Framework-independent business logic
  - Easier unit testing
  - Consistent organization across services
  - Frontend scales naturally with new features
  - Easier onboarding through predictable structure

- 🚫 **Disadvantages**
  - More folders and abstractions
  - Requires contributors to understand architectural boundaries
  - Slightly higher initial learning curve

---

## ✅ Decision

**We adopt:**

- **Clean Architecture** for every backend service.
- **Feature-Based Architecture** for the React frontend.

Backend services will follow the layered structure:

- Domain
- Application
- Infrastructure
- API

The frontend will organize code by business feature, with reusable code placed
under shared modules.

The exact directory layouts are documented separately in the architecture
documentation.

---

## 🔄 Consequences

### 🟢 Positive

* Every backend service follows the same organization.
* Business logic remains independent of FastAPI, SQLAlchemy and external
  libraries.
* Frontend features become self-contained and easier to evolve.
* New contributors can navigate the repository without learning a different
  structure for every service.
* Testing strategy naturally aligns with architectural boundaries.

### 🔴 Negative

* More boilerplate for small features.
* Developers must understand the responsibilities of each layer.
* Some files require passing through multiple layers before reaching the domain.

### 📌 Required Actions

1. [ ] Document the backend service structure.
2. [ ] Document the frontend project structure.
3. [ ] Apply this organization consistently across all services.
4. [ ] Review pull requests for compliance with the architectural boundaries.

---

## 🔗 Links

* `/docs/architecture/backend-service-structure.md`
* `/docs/architecture/frontend-structure.md`
