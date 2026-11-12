# Manual tests: user login (Log in page)

How to manually check the log in page against the ticket, using only the browser DevTools (Firefox). Each scenario lists the steps, the expected result and what to look at.

## Prerequisites

- The stack is running (frontend, `identity`, database) and `http://localhost:5173/login` loads.
- `identity` is healthy: `podman ps` shows it as `Up (healthy)`.
- You have **an existing account** (create one on `/signup` first, e.g. `login1@example.com` with password `12345678`), then log out.

## DevTools setup (once per session)

1. Open DevTools (`F12`) and go to the **Network** tab.
2. Tick **Persist log** so the list survives redirects. (you will find it by clicking on the wheel on the right, next to "no Throttling")
3. Click the trash icon to clear the list before each scenario.

## Things that look like errors but are not

- **`POST .../auth/login` in red with `401 Unauthorized`.** Firefox logs every 4xx/5xx response. This is expected when testing wrong credentials.
- **`POST .../auth/refresh` in red (`401` or `NS_BINDING_ABORTED`) at page load.** It comes from the session restoration in `AuthProvider`. A `401` only means "no session to restore" when the user is logged out. It is not related to the login form.
- **A request with no status in Offline mode.** No server response means no status code.

## Scenarios

### 1. Form validation (no request must be sent)

For each case, click **Log in** and check that:

- the expected message is displayed in red above the button,
- **no `login` request** appears in the Network tab,
- the button is still enabled.

| Input | Expected message |
|---|---|
| All fields empty | `Enter a valid email address` |
| Email `abc`, `abc@` or `abc@test` | `Enter a valid email address` |
| Valid email, empty password | `Password is required` |

### 2. Successful login

1. Fill the form with the email of an existing account (you can add spaces around it, e.g. `  login1@example.com  `) and its password.
2. Click **Log in**.

Expected:

- `POST /api/identity/auth/login` returns **200**.
- A `GET .../accounts/me` follows and returns **200**.
- The user is redirected to the dashboard `/dashboard/brief` (the profile is assumed complete at login until Personalization is connected) .
- The tabs *Morning Briefing* and *Saved Articles* are reachable.
- No error message is displayed.

### 3. Data sent to the server (URL and body)

**Goal:** check that the form sends the email and password **inside the request body**, never in the URL.

**Steps**

1. Clear the Network list (trash icon).
2. Fill the form with an existing email written with spaces around it and its password.
3. Click **Log in**.
4. In the Network tab, click the line named `login` (method `POST`).

**Check A: the URL (Headers tab, "Request URL")**

| Expected | Problem |
|---|---|
| `http://localhost:5173/api/identity/auth/login` | `.../login?email=...&password=...` |

Anything after a `?` means the browser submitted the form by itself instead of using our code. The password would then be visible in the address bar, the browser history and the server logs.

**Check B: the body (Request or Payload tab)**

Expected:

```json
{
  "email": "login1@example.com",
  "password": "your-test-password"
}
```

- `email` has **no spaces** around it (the code trims it).
- `password` is present and there is no other field.

### 4. Invalid credentials (401)

Run both sub-cases:

| Case | Input |
|---|---|
| A | Existing email, **wrong password** |
| B | Email that **does not exist**, any password |

For each one, check the **Response** tab of the `login` request: it must contain `code: "INVALID_CREDENTIALS"`.

Expected:

- Status **401**.
- Message `Invalid email or password` (the **same** message in both cases: the page must not reveal whether the email exists).
- The button is enabled again and the user stays on `/login`.
- The user is not logged in: opening `/dashboard/brief` redirects away from the dashboard.

### 5. Network error (Offline)

1. Load `/login`.
2. In the Network tab, change **No Throttling** to **Offline**.
3. Submit a valid form.

Expected:

- Message `Unable to reach the server`.
- The button is enabled again and the user stays on `/login`.

Set the menu back to **No Throttling** afterwards.

### 6. Generic server error

1. Stop the identity service: `podman stop identity`.
2. Submit a valid form.

Expected:

- `login` returns **502** (the Vite proxy cannot reach `identity`).
- Message `Something went wrong, please try again`.
- The button is enabled again.

Restart the service afterwards: `podman start identity`, and wait until it is healthy before testing again.

### 7. Loading state and double submission

1. Set the throttling menu to a slow profile (**GPRS** or **Regular 2G**).
2. Submit a valid form, then **click the button several times quickly**.

Expected:

- The button shows `Logging in...` and is disabled while waiting.
- **Only one** `login` request appears in the Network tab.
- The user is redirected to the dashboard at the end.

Set the menu back to **No Throttling** afterwards.

### 8. Authentication state is stored correctly

1. Log in successfully.
2. Open the **Storage** tab (DevTools).

Expected:

- **Cookies > `http://localhost:5173`**: a `refresh_token` cookie exists, flagged **HttpOnly**, with path `/api/identity/auth`.
- **Local Storage**: no access token and no `token` key. (Only the temporary `profileComplete` key may be there, until Personalization is connected.)
- **Session Storage**: only `lastPath` (the last visited page) may be there.

The password must not be stored anywhere.

### 9. Session remains active after a page refresh

1. Log in and open `/dashboard/brief`.
2. Press `F5`.

Expected:

- A `POST .../auth/refresh` returns **200**, followed by `GET .../accounts/me` **200**.
- A spinner may flash briefly, then the user is still on `/dashboard/brief` and still logged in.
- The user is **not** sent to the landing page or to `/login`.

### 10. Protected pages require authentication

1. Make sure you are logged out (use **Log out**, or a private window).
2. Type `http://localhost:5173/dashboard/brief` in the address bar. Repeat with `/dashboard/profile` and `/api-keys`.

Expected:

- Each time the user is redirected to the landing page (`/`).
- The dashboard content is never displayed, not even for a moment.

### 11. Sign out

1. Log in, then click **Log out**.

Expected:

- `POST /api/identity/auth/logout` returns **204**.
- The user leaves the dashboard.
- The `refresh_token` cookie is gone from the **Storage** tab.
- Pressing the browser's back button, or typing `/dashboard/brief`, does not show the dashboard again.
- Press `F5`: the user stays logged out.

## Moving to other pages

- A user who is already logged in and types `/login` or `/signup` in the address bar must **stay on the page they were on** (for example `/dashboard/brief`, or the landing page), not see the form again.
  1. Log in and go to `/dashboard/brief`. Type `/login`: the user comes back to `/dashboard/brief`.
  2. Go to the landing page `/`. Type `/signup`: the user comes back to `/`.
  3. Log out, then log in again: the previous `lastPath` must not be reused (the user lands on the default dashboard page).
  4. Let the session expire (or delete the `refresh_token` cookie and press `F5` on `/dashboard/profile`), then log in again: the user comes back to `/dashboard/profile` (the last visited page).

## Cleanup checklist

- [ ] Throttling is back to **No Throttling**.
- [ ] `identity` is running again (`podman ps`).
- [ ] Test accounts created during the session are no longer needed (or can be removed from the database, e.g. with Adminer).

## Known limitations

- The `VALIDATION_ERROR` message (`Some fields are invalid, please check your input`): the front end blocks an invalid email before the API call, so this case is hard to trigger by hand.
- Accessibility beyond keyboard navigation (Tab order, Enter to submit) and the `role="alert"` on the error message. A Lighthouse accessibility audit is a good complement.