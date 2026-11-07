# Manual tests: profile editing page

How to manually check the profile editing page. Each scenario lists the steps, the expected result and what to look at.

---

## Prerequisites

- The stack is running (frontend, identity, personalization, database and API gateway) and `http://localhost:8443` loads.
- The user is registered and logged in.
- The user already has a profile containing a name and interests.
- The API gateway is healthy and forwards Personalization requests correctly.

## DevTools setup (once per session)

1. Open DevTools (**F12**) and go to the **Network** tab.
2. Tick **Persist log** so the list survives redirects. (You will find it by clicking on the wheel on the right, next to "No Throttling".)
3. Click the trash icon to clear the list before each scenario.

## Things that look like errors but are not

- `POST .../auth/refresh` in red (`NS_BINDING_ABORTED`) at page load. It comes from session restoration in `AuthProvider`, not from the profile editing flow.
- Requests returning **401** when testing unauthenticated access. This is expected when the user is not authenticated.
- Requests returning **4xx or 5xx** in red in the console. The console logs unsuccessful HTTP responses. This is expected when testing error scenarios.
- A request with no status in **Offline** mode. No server response means no status code.

---

## Scenarios

### 1. Access the profile editing page

**Steps**

1. Log in with an existing account that has completed onboarding.
2. Navigate to the profile editing page.
3. Open the Network tab and inspect the requests.

**Expected**

- The profile editing page loads successfully.
- `GET /api/personalization/me/profile` returns **200**.
- `GET /api/personalization/topics` returns **200**.
- The existing name is displayed in the form.
- The existing interests are selected.
- No credential fields are displayed.
- No error message is displayed.

### 2. Existing profile information is displayed

**Goal:** check that the form is pre-filled with the current profile information.

**Steps**

1. Open the profile editing page.
2. Inspect the name field and selected interests.
3. Compare their values with the profile information returned by the API.

**Expected**

- The name field contains the existing name.
- The displayed name matches the `name` field returned by `GET /me/profile`.
- The existing interests are correctly selected.
- The selected interests match the `topic_ids` returned by `GET /me/profile`.
- The user can edit both the name and the selected interests.

**Network check**

Click the profile request (method `GET`) in the Network tab.

Expected response example:

```json
{
  "name": "Name",
  "topic_ids": ["business", "entertainment", "health"],
  "created_at": "2026-11-06T12:45:41.157427Z",
  "updated_at": "2026-11-06T12:45:41.157427Z"
}
```

Also inspect `GET /api/personalization/topics`.

Expected response example:

```json
{
  "items": [
{ "id": "business" },
    { "id": "entertainment" },
    { "id": "health" },
    { "id": "technology" },
    { "id": "science" },
    { "id": "sports" },
    { "id": "general" }
  ]
}
```

### 3. Client-side validation (no request must be sent)

**Goal:** check that invalid values are rejected before reaching the API.

For each case, enter the invalid value and click the update button.

**Expected**

- A validation message is displayed.
- No `PUT /api/personalization/me/profile` request appears in the Network tab.
- The user stays on the profile editing page.

| Input | Expected result |
| --- | --- |
| Empty name | Validation error |
| Name containing only spaces | Validation error |
| Name exceeding 50 characters after trimming | Validation error |
| No interest selected | Validation error |
| More than 4 interests selected | Prevented by the interface or validation error |
| Valid name and 1 interest | No validation error |
| Valid name and 4 interests | No validation error |

> **Note:** the name must contain between 1 and 50 characters after trimming. Interest IDs must be valid, without duplicates.

### 4. Successful profile update

**Steps**

1. Enter a new valid name (e.g. `Updated Test User`).
2. Modify the selected interests (e.g. `["business", "technology"]`).
3. Click the Save button.

**Expected**

- `PUT /api/personalization/me/profile` returns **200 OK**.
- A success confirmation is displayed.
- The updated name remains in the form.
- The updated interests remain selected.
- The submit button is enabled again.
- No error message is displayed.

**Network check**

Click the profile request (method `PUT`).

Expected request body example:

```json
{
  "name": "Updated Test User",
  "topic_ids": ["business", "technology"]
}
```

Check that:

- The modified name is sent in the request body.
- The selected interests are sent as `topic_ids`.
- The request uses `PUT`, not `PATCH` or `POST`.
- The request URL does not contain profile information as query parameters.
- Authentication credentials or the JWT are attached to the request: you will find this info by clicking on "PUT profile", then headers and look for the Request Header box, an Authentication line should be there, starting with "Bearer ..."

### 5. Failed update (server error)

**Goal:** check that the form preserves the user's input when the API fails.

**Steps**

1. Change the name to `New Name`.
2. Modify the selected interests.
3. Temporarily stop the Personalization service.


4. Click the Save button.

**Expected**

- The `PUT` request fails.
- An error message is displayed.
- The user stays on the profile editing page.
- The name field still contains `New Name`.
- The modified interests remain selected.
- The entered values are not replaced by the previous profile information.
- The user can retry the update.

**Cleanup**

Restart the service Personnalization.


Wait until it is healthy before continuing.

> **Note:** the gateway may return a **502** or another gateway error when the service is unavailable. The important point is that the frontend handles the failure correctly.

### 6. Loading state and double submission

**Steps**

1. Set the throttling menu to a slow profile (**GPRS** or **Regular 2G**).
2. Change the name and selected interests.
3. Click the update button, then click it several times quickly.

**Expected**

- The button shows a loading state (e.g. `Saving...`).
- The button is disabled while the request is running.
- Only **one** `PUT` request appears in the Network tab.
- The user cannot submit the form multiple times while waiting.
- The success confirmation appears when the request finishes.

> Set the menu back to **No Throttling** afterwards.

### 7. Unauthenticated user access

**Goal:** check that users who are not logged in cannot access the profile editing page.

**Steps**

1. Log out.
2. Navigate directly to the profile editing URL (copy the URL before logging out).
3. Observe the page and Network tab.

**Expected**

- The user is redirected to the landing page.
- The profile editing form is not accessible.
- No profile information is displayed.
- No successful `GET /me/profile` response is returned.
- The user cannot update the profile.

### 8. Authentication is attached to profile requests

**Goal:** check that profile requests are authenticated.

**Steps**

1. Log in.
2. Open the profile editing page.
3. Select the `GET /api/personalization/me/profile` request in the Network tab.
4. Open the **Headers** tab.

**Expected**

- The request contains the authentication credentials or token.
- If the application uses JWT, the request contains an authorization header similar to:

  ```http
  Authorization: Bearer <token>
  ```

- The API accepts the request and returns **200**.

Repeat the check for:

- `GET /api/personalization/topics`
- `PUT /api/personalization/me/profile`

### 9. Profile persistence after logout and login

**Goal:** check that the complete profile is saved in the backend and correctly retrieved when the user logs in again.

**Steps**

1. Log in with an existing account.
2. Open the profile editing page.
3. Note the current name and selected interests.
4. Change the name to `Persistent`.
5. Change the selected interests (e.g. `["business", "technology"]`).
6. Save the changes.
7. Check that the success confirmation appears.
8. Log out.
9. Log in again with the same account.
10. Navigate to the profile editing page.

**Expected**

- The user can log out and log in successfully.
- The profile editing page is accessible after login.
- `GET /api/personalization/me/profile` returns **200**.
- The name is still `Persistent`.
- The selected interests are still `business` and `technology`.
- The form is pre-filled with the updated profile.
- The user does not need to complete onboarding again.

**Network check**

- Inspect the `GET /me/profile` request after logging in again.
- Check that the response contains the updated `name` and `topic_ids`.

### 10. Newly registered user without a completed profile

**Goal:** check what happens when a user registers but does not complete profile onboarding.

**Steps**

1. Sign up using a new email address.
2. Do not complete profile onboarding.
3. Log out.
4. Log in again with the same account.
5. Navigate to the profile editing page.

**Expected**

- The user can log out and log in successfully.
- Identity authentication works independently of whether a Personalization profile exists.
- `GET /api/personalization/me/profile` returns **404 Not Found** with `PROFILE_NOT_FOUND`.
- The frontend handles the missing profile correctly.
- The user is redirected to the profile creation/onboarding page, where the name and interests can be completed.
- No application crash occurs.
- After completing the form, the frontend sends a PUT request that creates the profile (201).

> **Important:** according to the Personalization contract, a missing profile is represented by `404 PROFILE_NOT_FOUND`.

### 11. Newly registered user with a completed profile

**Goal:** check that a newly registered user's profile information persists after logout and login.

**Steps**

1. Register a new account using a new email address.
2. Complete profile onboarding.
3. Enter a name (e.g. `New User`).
4. Select between 1 and 4 interests.
5. Finish the onboarding flow.
6. Log out.
7. Log in again with the same account.
8. Navigate to the profile editing page.

**Expected**

- The user can log in successfully.
- The profile editing page is accessible.
- The existing name is automatically retrieved.
- The name field contains `New User`.
- The previously selected interests are automatically selected.
- The user does not need to complete onboarding again.
- The profile information is not lost after logout.

**Network check**

- Inspect the `GET /api/personalization/me/profile` response.
- Check that it contains the name and interests entered during onboarding.


---

## Cleanup checklist

- [ ] Throttling is back to **No Throttling**.
- [ ] Backend services stopped during testing have been restarted.
- [ ] All services are healthy (`make vm-ps`).
- [ ] The profile has been restored to its original name and interests if necessary.
- [ ] The user is logged out if the testing session is finished.

## Moving to other pages

- A user who is not logged in tries to access the profile editing page.
- A logged-in user navigates away from the page while an update is in progress.
- A user refreshes the page after successfully updating their profile.
- A user registers but does not complete profile onboarding.
- A user completes onboarding, logs out and logs in again.
- A user tries to access profile editing while the topics catalog is unavailable.
