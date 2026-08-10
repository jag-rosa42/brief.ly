# Backend Service Template

This folder is a **template for creating a new backend service** in the Transcendence project.

It provides the common structure, configuration, database setup, Alembic migration setup, testing setup, and development tooling that every backend service is expected to have.

When creating a new backend service, **copy this entire folder** and rename the `backend-service` directory to the name of the new service.

For example:

```text
backend-service/
```

can be copied as:

```text
identity/
```

or:

```text
personalization/
```

## Purpose

The goal of this template is to avoid recreating the same backend boilerplate for every service.

A new service created from this template already includes:

* Python project configuration with `pyproject.toml`
* `uv` dependency management
* FastAPI application entry point
* API structure
* Infrastructure/database structure
* SQLAlchemy database configuration
* Database sessions and engine configuration
* Alembic migrations
* Pytest test structure
* Ruff linting
* Type checking
* Make commands for common development tasks
* A standard project layout shared by backend services

The template should provide the **starting point**, not necessarily the final implementation of the service.

---

## Creating a New Service

To create a new backend service:

### 1. Copy the template

Copy the entire `backend-service` directory into:

```text
srcs/services/
```

For example:

```text
srcs/services/
├── identity/
├── personalization/
├── content-management/
└── ...
```

### 2. Rename the directory

The directory name should match the name of the new service.

For example:

```text
backend-service → identity
```

### 3. Search for `TODO`

The template intentionally contains `TODO` comments in files where **service-specific changes are required**.

After copying the template, search the entire new service directory for:

```text
TODO
```

For example:

```bash
grep -R "TODO" .
```

or, if using VS Code, use **Search in Files** and search for `TODO`.

Every relevant `TODO` should be reviewed and adapted to the new service.

> **Do not assume that the template is ready to run immediately after copying it.**

Some values are intentionally left as placeholders because they depend on the name and configuration of the new service.