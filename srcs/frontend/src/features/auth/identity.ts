import { apiFetch, CSRF_HEADER, session } from "@/shared/components/api/client";
import type { Account, TokenResponse } from "@/features/auth/types";

// 201 + refresh cookie set. Errors: 409 EMAIL_ALREADY_REGISTERED, 422 VALIDATION_ERROR.
export async function register(email: string, password: string): Promise<void> {
	const body = await apiFetch<TokenResponse>(`/api/identity/auth/register`, {
		method: "POST",
		body: { email, password },
		auth: false,
	});
	session.setAccessToken(body.access_token);
}

export async function login(email: string, password: string): Promise<void> {
	const body = await apiFetch<TokenResponse>(`/api/identity/auth/login`, {
		method: "POST",
		body: { email, password },
		auth: false,
	});
	session.setAccessToken(body.access_token);
}

// Always 204 once the CSRF header is sent; the cookie is cleared server-side.
export async function logout(): Promise<void> {
	try {
		await apiFetch<void>(`/api/identity/auth/logout`, {
			method: "POST",
			headers: CSRF_HEADER,
			auth: false,
		});
	} catch {
		// Server unreachable: the local session is cleared below anyway.
	} finally {
		session.setAccessToken(null);
	}
}

// Session bootstrap, on app start: the access token was lost with the page
// reload, but the refresh cookie may still be valid.
// Returns true if the user is still logged in.
export async function restoreSession(): Promise<boolean> {
	return (await session.refresh()) !== null;
}

export function getMe(signal?: AbortSignal): Promise<Account> {
	return apiFetch<Account>(`/api/identity/accounts/me`, { signal });
}