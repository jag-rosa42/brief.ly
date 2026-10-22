// Identity calls used by the frontend. Contract: docs/api/01_identity.md

import { apiFetch, CSRF_HEADER, refreshAccessToken, setAccessToken } from "@/shared/components/api/client";

const BASE = "/api/identity";

interface TokenResponse {
	access_token: string;
	token_type: "Bearer";
}

export interface Account {
	id: string;
	email: string;
	created_at: string; // ISO 8601 UTC
}

// 201 + refresh cookie set. Errors: 409 EMAIL_ALREADY_REGISTERED, 422 VALIDATION_ERROR.
export async function register(email: string, password: string): Promise<void> {
	const body = await apiFetch<TokenResponse>(`${BASE}/auth/register`, {
		method: "POST",
		body: { email, password },
		auth: false,
	});
	setAccessToken(body.access_token);
}

// 200 + refresh cookie set. Errors: 401 INVALID_CREDENTIALS, 422 VALIDATION_ERROR.
export async function login(email: string, password: string): Promise<void> {
	const body = await apiFetch<TokenResponse>(`${BASE}/auth/login`, {
		method: "POST",
		body: { email, password },
		auth: false,
	});
	setAccessToken(body.access_token);
}

// Always 204 once the CSRF header is sent; the cookie is cleared server-side.
export async function logout(): Promise<void> {
	try {
		await apiFetch<void>(`${BASE}/auth/logout`, {
			method: "POST",
			headers: CSRF_HEADER,
			auth: false,
		});
	} finally {
		setAccessToken(null);
	}
}

// Session bootstrap, on app start: the access token was lost with the page
// reload, but the refresh cookie may still be valid.
// Returns true if the user is still logged in.
export async function restoreSession(): Promise<boolean> {
	return (await refreshAccessToken()) !== null;
}

export function getMe(signal?: AbortSignal): Promise<Account> {
	return apiFetch<Account>(`${BASE}/accounts/me`, { signal });
}