# Services

## 1. Purpose

This document describes the responsibilities and boundaries of each backend
service.

A service represents a business capability.

A service should:

- Own its business rules.
- Own its data.
- Expose a clear API.
- Avoid depending directly on another service's implementation.

---

## 2. Service Overview

| Service | Responsibility |
|---------|----------------|
| Identity | User authentication and account management |
| Personalization | User preferences and customization |
| Content Management | Articles and content lifecycle |
| AI Processing | AI-based content processing |
| Morning Briefing | Personalized briefing generation |
| Administration | Administrative operations |

---

## 3. Identity Service

### 3.1 Responsibility

The Identity Service manages user identity and authentication.

### 3.2 Owns

- User accounts
- Credentials
- Authentication tokens
- Sessions
- Password management

### 3.3 Does Not Own

- User preferences
- User-generated content
- Application-specific profiles

### 3.4 Example Capabilities

- Register user
- Login
- Refresh token
- Reset password
- Validate identity

---

## 4. Personalization Service

### 4.1 Responsibility

The Personalization Service manages user-specific preferences and experiences.

### 4.2 Owns

- User preferences
- Settings
- Customization options
- User interests

### 4.3 Does Not Own

- Authentication credentials
- Content storage

### 4.4 Example Capabilities

- Update preferences
- Manage reading preferences
- Store user configuration

---

## 5. Content Management Service

### 5.1 Responsibility

The Content Management Service manages application content.

### 5.2 Owns

- Articles
- Posts
- Content metadata
- Publication state

### 5.3 Does Not Own

- User accounts
- User preferences

### 5.4 Example Capabilities

- Create content
- Update content
- Publish content
- Search content

---

## 6. AI Processing Service

### 6.1 Responsibility

The AI Processing Service handles AI-related operations.

### 6.2 Owns

- AI processing workflows
- Generated results
- Processing metadata

### 6.3 Does Not Own

- Original content ownership
- User authentication

### 6.4 Example Capabilities

- Content summarization
- Classification
- Recommendation processing

---

## 7. Morning Briefing Service

### 7.1 Responsibility

The Morning Briefing Service creates personalized daily summaries.

### 7.2 Owns

- Briefing generation
- Briefing history
- Delivery preferences

### 7.3 Depends On

- Personalization Service
- Content Management Service
- AI Processing Service

### 7.4 Example Capabilities

- Generate daily briefing
- Retrieve previous briefings

---

## 8. Administration Service

### 8.1 Responsibility

The Administration Service provides administrative capabilities.

### 8.2 Owns

- Administrative actions
- System configuration
- Management operations

### 8.3 Example Capabilities

- Manage users
- Monitor services
- Configure application settings

---

## 9. Service Boundaries

### 9.1 Services Should Communicate Through APIs

Good:

```text
Content Service

        |
        | HTTP/API request
        ▼

AI Processing Service
```

Bad:

```text
Content Service

        |
        ▼

Direct database access

        |
        ▼

AI Processing Database
```

---

## 10. Data Ownership Rules

Each service owns its data.

Rules:

- No shared databases.
- No direct database access between services.
- No duplicated ownership of the same business concept.

Example:

The Identity Service owns:

```text
User authentication data
```

The Personalization Service may reference:

```text
user_id
```

but does not store authentication information.

---

## 11. Adding a New Service

Before creating a new service, answer:

1. Does this represent a separate business capability?
2. Does it require independent evolution?
3. Does it own unique data?
4. Does it have a clear API boundary?

If not, the functionality may belong inside an existing service.

---

## 12. Related Documentation

- `overview.md`
- `backend-service-structure.md`
- ADR-0004 — Adopt Clean Architecture and Feature-Based Architecture
