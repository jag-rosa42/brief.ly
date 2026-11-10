# Manual tests: Public API Keys page

How to manually check the Public API Keys page. Each scenario lists the steps, the expected result and what to look at.

## Prerequisites

- The stack is running (frontend, Identity, database and API gateway) and <http://localhost:8443> loads.
- The user is registered and logged in.
- The API gateway is healthy and forwards Identity requests correctly.
- The Identity API Keys endpoints are implemented and available:
  - `GET /api/identity/api-keys`
  - `POST /api/identity/api-keys`
  - `DELETE /api/identity/api-keys/{key_id}`

## DevTools setup (once per session)

1. Open DevTools (`F12`) and go to the **Network** tab.
2. Tick **Persist log** so the list survives redirects.
3. Click the trash icon to clear the list before each scenario.

### Things that look like errors but are not

- `POST .../auth/refresh` in red (`NS_BINDING_ABORTED`) at page load. It comes from session restoration in `AuthProvider`, not from the API keys flow.
- Requests returning `401` when testing unauthenticated access. This is expected.
- Requests returning 4xx or 5xx in red in the console. The console logs unsuccessful HTTP responses. This is expected when testing error scenarios.
- A request with no status in Offline mode. No server response means no status code.

---

## Scenarios

### 1. Access the Public API Keys page

**Steps**

1. Log in with an existing account.
2. Navigate to the Public API Keys page.
3. Open the Network tab and inspect the requests.

**Expected**

- The Public API Keys page loads successfully.
- `GET /api/identity/api-keys` is sent and returns `200 OK`.
- The API keys list is displayed.
- No error message is displayed.
- The number of active keys is displayed (e.g. `2 / 5`).

---

### 2. Empty state

**Goal:** check that the page handles an account without API keys.

**Steps**

1. Make sure the account has no active API keys.
2. Open the Public API Keys page.
3. Inspect the Network tab.

**Expected**

- `GET /api/identity/api-keys` returns `200 OK`.
- The response contains an empty `items` array:

  ```json
  {
    "items": []
  }
  ```

- The message **No API key yet.** is displayed.
- The counter displays `0 / 5`.
- The user can start creating an API key.

---

### 3. Existing API keys are displayed

**Goal:** check that the page correctly displays the API keys returned by Identity.

**Steps**

1. Create one or more API keys beforehand, or use an account that already has active keys.
2. Open the Public API Keys page.
3. Inspect the displayed keys.
4. Compare them with the response returned by `GET /api/identity/api-keys`.

**Expected**

- Each API key displays:
  - its name,
  - its prefix, followed by masked characters,
  - its permissions (`read`, `write` or both),
  - its expiration date and time,
  - its status (**Active** or **Expired**).
- The newest keys appear first.
- The counter displays the number of active keys out of 5.
- The full API key is **never** displayed in the list.

**Network check**

Expected response example:

```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "My script",
      "prefix": "tr_8f3k",
      "scopes": ["read", "write"],
      "created_at": "2026-11-09T10:00:00Z",
      "expires_at": "2026-11-11T10:00:00Z"
    }
  ]
}
```

Check that:

- The response contains `items`.
- Each item contains the expected fields.
- No `key` field is returned.
- The expiration date is 48 hours after creation.

---

### 4. Client-side validation (no request must be sent)

**Goal:** check that invalid API key names and permissions are rejected before reaching Identity.

For each case, enter the value and click the **Create** button.

**Expected for invalid input**

- A validation message is displayed.
- No `POST /api/identity/api-keys` request appears in the Network tab.
- The user stays on the page.

| Input                                        | Expected result     |
| -------------------------------------------- | ------------------- |
| Empty name                                   | Validation error    |
| Name containing only spaces                  | Validation error    |
| Name exceeding 50 characters after trimming  | Validation error    |
| No permission selected                       | Validation error    |
| Valid name and `read` permission             | No validation error |
| Valid name and `write` permission            | No validation error |
| Valid name and both permissions              | No validation error |

> **Note:** the name must contain between 1 and 50 characters after trimming. At least one permission must be selected.

---

### 5. Successful API key creation

**Goal:** check that the frontend correctly creates an API key and displays the full key only once.

**Steps**

1. Open the Public API Keys page.
2. Click the **+** button.
3. Enter a valid name (e.g. `My script`).
4. Select one or both permissions.
5. Click **Create**.
6. Confirm the creation in the confirmation dialog.

**Expected**

- `POST /api/identity/api-keys` is sent and returns `201 Created`.

- The full API key is displayed immediately after creation.
- The user can save the key.
- The user is informed that the full key cannot be retrieved again.
- The newly created API key appears in the list, at the top, without requiring a page reload.
- The creation form is reset.
- The counter is updated.

**Network check**

Expected request body:

```json
{
  "name": "My script",
  "scopes": ["read", "write"]
}
```

Expected response example:

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "My script",
  "prefix": "tr_8f3k",
  "scopes": ["read", "write"],
  "created_at": "2026-11-09T10:00:00Z",
  "expires_at": "2026-11-11T10:00:00Z",
  "key": "tr_8f3k..."
}
```

Check that:

- The request uses `POST`.
- The name and scopes are sent in the request body.
- The response contains the full key.
- The response contains an expiration date 48 hours after creation.
- The full key is not sent in subsequent requests.

---

### 6. API key expiration

**Goal:** check that the expiration date and time are correctly displayed.

**Steps**

1. Create a new API key.
2. Inspect its expiration date and time in the API keys list.
3. Compare it with the `created_at` and `expires_at` values returned by the `POST` response.

**Expected**

- The expiration date is displayed in a readable format.
- Both the date and the exact time are visible.
- The expiration date is exactly 48 hours after creation.
- A non-expired key displays **Active**.
- An expired key displays **Expired**.
- An expired key is not included in the backend's active keys list.

> **Note:** Identity is responsible for excluding expired keys from `GET /api/identity/api-keys`. The frontend displays the status based on the returned expiration date.

---

### 7. API key limit reached (409)

**Goal:** check that the frontend correctly handles the maximum number of active API keys.

**Steps**

1. Make sure the account already has 5 active API keys.
2. Open the Public API Keys page.
3. Try to create another API key.

**Expected**

- The counter displays `5 / 5`.
- The **+** button is disabled.
- The user cannot open the creation form.
- If the backend independently returns `409 Conflict` with `API_KEY_LIMIT_REACHED`, the frontend displays an appropriate error message.
- The existing keys remain unchanged.

**Network check**

Expected response:

```json
{
  "error": {
    "code": "API_KEY_LIMIT_REACHED",
    "message": "..."
  }
}
```

---

### 8. Successful API key revocation

**Goal:** check that the user can revoke an existing API key.

**Steps**

1. Open the Public API Keys page.
2. Click **Delete** next to an existing API key.
3. Confirm the deletion in the confirmation dialog.
4. Inspect the Network tab.

**Expected**

- `DELETE /api/identity/api-keys/{key_id}` is sent and returns `204 No Content`.
- The API key disappears from the list.
- The counter decreases by one.
- The user receives the updated list.
- No page reload is required.

**Network check**

Check that:

- The request uses `DELETE`.
- The URL contains the correct API key UUID.
- The request includes the Bearer access token.
- The response status is `204`.
- No response body is expected.

---

### 9. Failed API key creation

**Goal:** check that the frontend correctly handles API errors.

**Steps**

1. Open the creation form.
2. Enter a valid name and select at least one permission.
3. Confirm the creation.
4. Simulate a server error or temporarily make Identity unavailable.

**Expected**

- The `POST` request fails.
- An error message is displayed.
- The user stays on the page.
- The existing API keys remain unchanged.
- The creation form can be opened again.
- The user can retry the operation.

> **Note:** the gateway may return a `502`, `503` or `504` when Identity is unavailable.

---

### 10. Unauthenticated user access

**Goal:** check that users who are not logged in cannot access the Public API Keys page.

**Steps**

1. Log out.
2. Navigate directly to the Public API Keys page URL.
3. Observe the page and the Network tab.

**Expected**

- The user is redirected to the landing page.
- The API Keys page is not accessible.
- No API key information is displayed.
- No successful API keys request is returned.

---

### 11. Authentication is attached to API key requests

**Goal:** check that all API key requests are authenticated.

**Steps**

1. Log in.
2. Open the Public API Keys page.
3. Select the `GET /api/identity/api-keys` request in the Network tab.
4. Open the **Headers** tab.

**Expected**

The request contains an authorization header similar to:

```http
Authorization: Bearer <token>
```

Repeat the check for:

- `POST /api/identity/api-keys`
- `DELETE /api/identity/api-keys/{key_id}`

Check that:

- All requests use the Bearer access token.
- The token is not included in the request body or URL.
- The requests are sent through the existing `apiFetch` client.

---

### 12. API key persistence after logout and login

**Goal:** check that API keys are associated with the user's account and persist across sessions.

**Steps**

1. Log in with an existing account.
2. Open the Public API Keys page.
3. Create an API key.
4. Note its name and prefix.
5. Log out.
6. Log in again with the same account.
7. Navigate to the Public API Keys page.

**Expected**

- The user can log out and log in successfully.
- `GET /api/identity/api-keys` returns `200 OK`.
- The previously created API key appears in the list.
- Its name, prefix, scopes and expiration date are preserved.
- The full API key is not displayed again.
- The user can still revoke the key.

---

## Additional edge cases to try

- [ ] A user opens the API Keys page while a request is in progress.
- [ ] A user navigates away immediately after creating an API key.
- [ ] A user refreshes the page after creating an API key.
- [ ] A user attempts to create a sixth active API key.
- [ ] A user tries to revoke an already revoked API key.
- [ ] A user attempts to access another account's API keys.
- [ ] A user's API key expires while the page is open.

## Cleanup checklist

- [ ] Throttling is back to **No Throttling**.
- [ ] Any services stopped during testing have been restarted.
- [ ] All services are healthy (`make vm-ps`).
- [ ] Unnecessary test API keys have been revoked.
- [ ] The user is logged out if the testing session is finished.
