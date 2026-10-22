# Manual tests: user registration (Sign up page)

How to manually check the sign up page against the ticket, using only the browser DevTools (Firefox). Each scenario lists the steps, the expected result and what to look at.

## Prerequisites

- The stack is running (frontend, `identity`, database) and `http://localhost:5173/signup` loads.
- `identity` is healthy: `podman ps` shows it as `Up (healthy)`.
- Use a **new email** for every successful registration (e.g. `test1@example.com`, `test2@example.com`). Registering the same email twice returns a 409.

## DevTools setup (once per session)

1. Open DevTools (`F12`) and go to the **Network** tab.
2. Tick **Persist log** so the list survives redirects. (you will find it by clicking on the wheel on the right, next to "no Throttling")
3. Click the trash icon to clear the list before each scenario.

## Things that look like errors but are not

- **`POST .../auth/refresh` in red (`NS_BINDING_ABORTED`) at page load.** It comes from the session restoration in `AuthProvider`, not from the form. It is not related to the sign up flow.
- **`XHR POST .../register [HTTP/1.1 409 Conflict]` in the Console.** Firefox logs every 4xx/5xx response. This is expected when testing error cases.
- **A request with no status in Offline mode.** No server response means no status code.

## Scenarios

### 1. Form validation (no request must be sent)

For each case, click **Sign up** and check that:

- the expected message is displayed in red above the button,
- **no `register` request** appears in the Network tab,
- the button is still enabled.

| Input | Expected message |
|---|---|
| All fields empty | `Enter a valid email address` |
| Email `abc`, `abc@` or `abc@test` | `Enter a valid email address` |
| Valid email, password of 7 characters | `Password must be at least 8 characters` |
| Valid email, different passwords | `Passwords do not match` |

### 2. Successful registration

1. Fill the form with a new email, surrounded by spaces (e.g. `  test1@example.com  `), a password of at least 8 characters, and the same value in the confirmation field.
2. Click **Sign up**.

Expected:

- `POST /api/identity/auth/register` returns **201**.
- A `GET .../me` follows and returns **200**.
- The page URL becomes **`/dashboard/profile`**.
- No error message is displayed.

### 3. Data sent to the server (URL and body)
 
**Goal:** check that the form sends the email and password **inside the request body**, never in the URL, and that only the needed fields are sent.
 
**Steps**
 
1. Clear the Network list (trash icon).
2. Fill the form with a new email written with spaces around it (e.g. `  test2@example.com  `), a password of at least 8 characters, and the same password in the confirmation field.
3. Click **Sign up**.
4. In the Network tab, click the line named `register` (method `POST`).
**Check A: the URL (Headers tab, "Request URL")**
 
| Expected | Problem |
|---|---|
| `http://localhost:5173/api/identity/auth/register` | `.../register?email=test2@example.com&password=...` |
 
Anything after a `?` means the browser submitted the form by itself instead of using our code. The password would then be visible in the address bar, the browser history and the server logs.
 
**Check B: the body (Request or Payload tab)**
 
Expected:
 
```json
{
  "email": "test2@example.com",
  "password": "your-test-password"
}
```
 
- `email` has **no spaces** around it (the code trims it).
- `password` is present.
- There is **no `confirmPass`**: that field is only used in the browser to check that both passwords match, so the server does not need it.


### 4. Email already registered (409)

1. Register an email that already exists (use the one from scenario 2).
2. Check the **Response** tab of the `register` request: it must contain `code: "EMAIL_ALREADY_REGISTERED"`.

Expected:

- Status **409**.
- Message `This email is already registered`.
- The button is enabled again and the user stays on `/signup`.

### 5. Network error (Offline)

1. Load `/signup`.
2. In the Network tab, change **No Throttling** to **Offline**.
3. Submit a valid form with a new email.

Expected:

- Message `Unable to reach the server`.
- The button is enabled again and the user stays on `/signup`.

Set the menu back to **No Throttling** afterwards.

### 6. Generic server error

1. Stop the identity service: `podman stop identity`.
2. Submit a valid form with a new email.

Expected:

- `register` returns **502** (the Vite proxy cannot reach `identity`).
- Message `Something went wrong, please try again`.
- The button is enabled again.

Restart the service afterwards: `podman start identity`, and wait until it is healthy before testing again.

### 7. Loading state and double submission

1. Set the throttling menu to a slow profile (**GPRS** or **Regular 2G**).
2. Submit a valid form with a new email, then **click the button several times quickly**.

Expected:

- The button shows `Signing up...` and is disabled while waiting.
- **Only one** `register` request appears in the Network tab.
- The user is redirected to `/dashboard/profile` at the end.

Set the menu back to **No Throttling** afterwards.

## Cleanup checklist

- [ ] Throttling is back to **No Throttling**.
- [ ] `identity` is running again (`podman ps`).
- [ ] Test accounts created during the session are no longer needed (or can be removed from the database, e.g. with Adminer).

## Not covered by these tests

- The `VALIDATION_ERROR` message (`Some fields are invalid, please check your input`): the front end blocks invalid input before the API call, so this case is hard to trigger by hand.
- A user who is already logged in and opens `/signup`.
- Accessibility beyond keyboard navigation (Tab order, Enter to submit) and the `role="alert"` on the error message. A Lighthouse accessibility audit is a good complement.
