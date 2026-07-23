# Frontend Structure

## Purpose

The frontend follows a **feature-based architecture**.

Rather than organizing files by technology (components, hooks, pages, etc.),
the application is organized around **business features**.

Each feature owns its UI components, API calls, hooks and types, making the
codebase easier to understand, maintain and extend.

The goals of this architecture are to:

- Group related code together.
- Reduce coupling between unrelated features.
- Encourage high cohesion within each feature.
- Make new features easy to add.
- Keep reusable code centralized.

---

# Overall Structure

```text
frontend/
├── src/
│   ├── features/
│   ├── shared/
│   ├── pages/
│   ├── app/
│   └── main.tsx
├── public/
├── index.html
└── package.json
```

---

# Feature-Based Organization

Every business capability lives inside its own feature.

Example:

```text
features/
├── auth/
├── profile/
├── articles/
├── game/
└── chat/
```

A feature owns everything required to implement that capability:

- API calls
- Components
- Hooks
- Types
- Local utilities (if needed)

A developer working on authentication should rarely need to leave
`features/auth`.

---

# Directory Responsibilities

## features/

```text
features/
└── auth/
    ├── api.ts
    ├── components/
    ├── hooks/
    └── types.ts
```

Contains business features.

Each feature should remain as self-contained as possible.

Typical contents:

- API requests
- Feature-specific React components
- Feature-specific hooks
- DTOs and TypeScript types
- Local helper functions

A feature should **not** contain reusable generic components.

---

## shared/

```text
shared/
├── api/
├── components/
├── hooks/
├── utils/
├── constants/
└── types/
```

Contains reusable code shared by multiple features.

Examples:

### components/

Reusable UI elements.

Examples:

- Button
- Modal
- Card
- Avatar
- Spinner
- Input

These components should have **no business knowledge**.

---

### api/

Shared API infrastructure.

Examples:

- Axios instance
- Fetch wrapper
- Authentication interceptor
- Error handling

Business-specific requests belong inside each feature.

---

### hooks/

Reusable hooks.

Examples:

- useDebounce()
- useLocalStorage()
- useClickOutside()

Feature-specific hooks remain inside the corresponding feature.

---

### utils/

Generic helper functions.

Examples:

- formatDate()
- truncateText()
- capitalize()

Avoid placing business logic here.

---

### constants/

Application-wide constants.

Examples:

- Routes
- Theme names
- LocalStorage keys
- Query keys

---

### types/

Types shared across multiple features.

Feature-specific types should remain inside the feature.

---

## pages/

```text
pages/
├── HomePage.tsx
├── LoginPage.tsx
├── DashboardPage.tsx
└── ProfilePage.tsx
```

Pages correspond to application routes.

A page should primarily compose existing feature components rather than contain
significant business logic.

Pages answer:

> Which features should be displayed together?

---

## app/

```text
app/
├── router.tsx
├── Layout.tsx
└── providers.tsx
```

Contains application bootstrap and global configuration.

Examples:

- React Router
- Theme Provider
- Query Client
- Authentication Provider
- Application Layout

This directory wires the application together.

---

## main.tsx

The React entry point.

Responsibilities include:

- Rendering the application.
- Mounting providers.
- Loading global styles.

---

# Dependency Rule

Dependencies should remain predictable.

```text
Pages
   │
   ▼
Features
   │
   ▼
Shared
```

Features may depend on Shared.

Pages may depend on Features.

Shared must never depend on Features.

This keeps reusable code independent of business concerns.

---

# Relationship with Backend Services

Frontend features generally correspond to backend business capabilities.

Example:

| Frontend Feature | Primary Backend Service |
|------------------|-------------------------|
| auth | Identity |
| profile | Personalization |
| articles | Content Management |
| game | Game Service |
| chat | Chat Service |

This mapping is conceptual rather than mandatory.

A frontend feature may communicate with multiple backend services when required.

---

# How to Decide Where Code Belongs

When adding new code, ask:

> "Is this specific to one business feature?"

If **yes**, place it inside that feature.

If **no**, place it inside `shared`.

| If you're writing... | Put it here |
|----------------------|-------------|
| Login form | `features/auth/components/` |
| Authentication API call | `features/auth/api.ts` |
| Authentication hook | `features/auth/hooks/` |
| Profile editor | `features/profile/components/` |
| Generic modal | `shared/components/` |
| Generic button | `shared/components/` |
| Axios instance | `shared/api/` |
| Date formatter | `shared/utils/` |
| React Router configuration | `app/router.tsx` |
| Theme Provider | `app/providers.tsx` |
| Dashboard page | `pages/` |
| Shared TypeScript types | `shared/types/` |

When in doubt:

- Business-specific → Feature
- Generic → Shared

---

# Common Mistakes

## ❌ Putting every component into shared/components

Only reusable components belong there.

If only the authentication feature uses a component, it belongs inside
`features/auth/components`.

---

## ❌ Calling the API directly from pages

Pages should compose features.

Business API calls belong inside the feature.

---

## ❌ Mixing business logic into shared utilities

Avoid:

```typescript
shared/utils/getLeaderboard.ts
```

This is business logic.

It belongs inside the Game feature.

---

## ❌ Sharing components too early

Do not move a component into `shared` simply because it *might* become reusable.

Wait until at least two features genuinely need it.

---

# Design Principles

When contributing to the frontend:

- Organize code by business feature.
- Keep features cohesive.
- Keep shared code framework-agnostic whenever possible.
- Prefer composition over duplication.
- Keep pages lightweight.
- Place business logic close to the feature that owns it.
- Extract to `shared` only after proven reuse.

---

# Code Review Checklist

Before approving a pull request, verify that:

- [ ] The new code belongs to the correct feature.
- [ ] Reusable components are generic and business-independent.
- [ ] Business logic remains inside the owning feature.
- [ ] Pages only compose features.
- [ ] Shared utilities remain generic.
- [ ] API calls are grouped inside the appropriate feature.
- [ ] New functionality includes appropriate tests where applicable.

---

# Related Documentation

- ADR-0004 — Adopt Clean Architecture for Backend Services and Feature-Based Architecture for the Frontend
- `backend-service-structure.md`
- `development-principles.md`
