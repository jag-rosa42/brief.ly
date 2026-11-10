# Personalization

Personalization owns the profile (a name plus 1 to 4 interests) and the saved articles. Topics and articles themselves belong to Content Management. There is no separate POST for the profile: PUT both creates and updates it.

It serves the same use cases through two doors: Frontend routes (browser token) and Public routes (API key). Both share the bodies below. It also serves the public API documentation page for both services that have Public routes. Conventions, tokens and errors are in [00_conventions.md](00_conventions.md).


| Kind | Method | Caller path | Service path | Auth | Success | Status |
| --- | --- | --- | --- | --- | --- | --- |
| Frontend | GET | `/api/personalization/me/profile` | `/me/profile` | Bearer | 200 | Done |
| Frontend | PUT | `/api/personalization/me/profile` | `/me/profile` | Bearer | 201 / 200 | Done |
| Frontend | GET | `/api/personalization/topics` | `/topics` | Bearer | 200 | Done |
| Frontend | GET | `/api/personalization/me/saved-articles` | `/me/saved-articles` | Bearer | 200 | Done |
| Frontend | POST | `/api/personalization/me/saved-articles/{article_id}` | `/me/saved-articles/{article_id}` | Bearer | 201 | Done |
| Frontend | DELETE | `/api/personalization/me/saved-articles/{article_id}` | `/me/saved-articles/{article_id}` | Bearer | 204 | Done |
| Public | GET | `/public/v1/topics` | same | API key (`read`) | 200 | To do |
| Public | GET | `/public/v1/me/profile` | same | API key (`read`) | 200 | To do |
| Public | PUT | `/public/v1/me/profile` | same | API key (`write`) | 201 / 200 | To do |
| Public | GET | `/public/v1/me/saved-articles` | same | API key (`read`) | 200 | To do |
| Public | POST | `/public/v1/me/saved-articles/{article_id}` | same | API key (`write`) | 201 | To do |
| Public | DELETE | `/public/v1/me/saved-articles/{article_id}` | same | API key (`write`) | 204 | To do |
| Public | GET | `/public/v1/docs` | same | None | 200 | To do |
| Public | GET | `/public/v1/openapi/personalization.json` | same | None | 200 | To do |
| Internal | GET | — | `/internal/v1/me/profile` | User (forwarded) | 200 | Done |
| Internal | GET | — | `/health` | None | 200 | Done |

Public routes answer like their Frontend twin, plus:

```text
401 Unauthorized      INVALID_API_KEY (from Identity, via the gateway),
                      with WWW-Authenticate: ApiKey header="X-API-Key"
403 Forbidden         INSUFFICIENT_SCOPE (key lacks read or write)
429 Too Many Requests rate limited by the gateway (per IP, then per key)
```

Public documentation:

- `/public/v1/docs` is a Swagger UI page served by Personalization. Swagger UI can show several OpenAPI documents with a selector; this page shows two: `/public/v1/openapi/personalization.json` (served by Personalization) and `/public/v1/openapi/morning-briefing.json` (served by Morning Briefing).
- Each document contains only that service's `/public/v1` routes.
- These three paths need no key: the gateway routes them without ForwardAuth.
- Each service's own `/docs` stays unrouted.

## Endpoint details

Each endpoint below shows the request and every possible response.

### GET /api/personalization/me/profile

Service path: `GET /me/profile`. Public twin: `GET /public/v1/me/profile`.

```text
Header: Authorization: Bearer <access token>

200 OK
{
  "name": str,
  "topic_ids": [str],                1-4 topic IDs, e.g. ["business", "technology"]
  "created_at": datetime,
  "updated_at": datetime
}
401 Unauthorized
404 Not Found         PROFILE_NOT_FOUND (frontend shows onboarding)
```

### PUT /api/personalization/me/profile (create or update)

Service path: `PUT /me/profile`. Public twin: `PUT /public/v1/me/profile`.

The first call creates the profile. After that, only the fields you send are changed.

```text
Header: Authorization: Bearer <access token>
Body:
{
  "name"?: str,              1-50 chars after trim
  "topic_ids"?: [str]        1-4 topic IDs, no duplicates
}

Rules:
  profile does not exist   name AND topic_ids required
  profile exists           at least one field; omitted fields unchanged

201 Created           profile created, same body as GET
200 OK                profile updated, same body as GET
401 Unauthorized
422 Unprocessable     VALIDATION_ERROR
                        - name or topic_ids missing on create
                        - empty body on update
                        - name length out of range
                        - topic_ids: fewer than 1, more than 4, duplicates
                        - unknown topic id (details list the invalid ids)
503 Unavailable       SERVICE_UNAVAILABLE (topic_ids sent, catalog unreachable)
```

### GET /api/personalization/topics

Service path: `GET /topics`. Public twin: `GET /public/v1/topics`.

Returns the topic catalog for the onboarding and profile pickers. It is served from Personalization's cached copy of Content Management's catalog, because Content Management is not reachable through the gateway.

```text
Header: Authorization: Bearer <access token>

200 OK
{
  "items": [{ "id": str }]           e.g. [{ "id": "business" }, ...]
}
401 Unauthorized
503 Unavailable       SERVICE_UNAVAILABLE
```

### GET /api/personalization/me/saved-articles

Service path: `GET /me/saved-articles`. Public twin: `GET /public/v1/me/saved-articles`.

Most recently saved first. The article fields are a snapshot taken at the moment the article was saved, copied from the article Content Management returned, summary included.

```text
Header: Authorization: Bearer <access token>

200 OK
{
  "items": [
    {
      "article_id": UUID,
      "title": str,
      "publisher_name": str,           copied from Content Management at save time
      "topic_id": str,
      "summary": str | null,           copied from Content Management at save time;
                                       null if the article was not summarized yet
      "url": str,
      "read_time_minutes": int,
      "saved_at": datetime
    }
  ]                           [] when nothing saved
}
401 Unauthorized
```

### POST /api/personalization/me/saved-articles/{article_id}

Service path: `POST /me/saved-articles/{article_id}`. Public twin: `POST /public/v1/me/saved-articles/{article_id}`.

Personalization calls `GET /internal/v1/articles/{article_id}` on Content Management with its service token, and stores the snapshot, summary included. It never calls AI Processing.
Content Management returns `ARTICLE_NOT_FOUND` for an unknown or rejected article,
so a rejected article cannot be added to saved articles. A snapshot that was
saved before a later rejection remains unchanged.

```text
Header: Authorization: Bearer <access token>
Body: none

201 Created           the saved item, same shape as one entry of GET
401 Unauthorized
404 Not Found         PROFILE_NOT_FOUND
404 Not Found         ARTICLE_NOT_FOUND (unknown or rejected in Content Management)
409 Conflict          ARTICLE_ALREADY_SAVED
409 Conflict          SAVED_ARTICLES_LIMIT_REACHED (max 12)
422 Unprocessable     VALIDATION_ERROR (article_id not a UUID)
503 Unavailable       SERVICE_UNAVAILABLE
```

### DELETE /api/personalization/me/saved-articles/{article_id}

Service path: `DELETE /me/saved-articles/{article_id}`. Public twin: `DELETE /public/v1/me/saved-articles/{article_id}`.

Idempotent: deleting an article that isn't saved also returns 204.

```text
Header: Authorization: Bearer <access token>

204 No Content
401 Unauthorized
422 Unprocessable     VALIDATION_ERROR (article_id not a UUID)
```

### GET /internal/v1/me/profile

Used by Morning Briefing to build the dashboard, with the token Morning Briefing received forwarded unchanged. The account comes from that token.

It accepts two audiences, because Morning Briefing has a Frontend route and a Public route:
- `transcendence:api`: the user's access token, when the request came from our React app
- `transcendence:public-api`: the public API token, when the request came from a script through `GET /public/v1/morning-briefing`

```text
Header: Authorization: Bearer <forwarded access token or public API token>

200 OK
{
  "account_id": UUID,
  "name": str,
  "topic_ids": [str],
  "saved_article_ids": [UUID]
}
401 Unauthorized
404 Not Found         PROFILE_NOT_FOUND
```
