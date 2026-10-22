// Small fetch wrapper for our API.
//
// - Adds "Authorization: Bearer <access token>" to protected calls.
// - Turns every error answer into an ApiError (status + code).
// - Refreshes the access token when it is about to expire, and once more
//   (then replays the request) when a call answers 401 TOKEN_EXPIRED.
//
// The access token lives only in this module's memory, never in localStorage.
// Contract: docs/api/00_conventions.md and docs/api/01_identity.md

const REFRESH_URL = "/api/identity/auth/refresh";
// Refresh ahead of time when the token has less than this left.
const REFRESH_MARGIN_SECONDS = 60;
const DEFAULT_TIMEOUT_MS = 10_000;

// CSRF guard: required by the two routes that read the refresh cookie
// (refresh and logout). Not a secret, see 00_conventions.md.
export const CSRF_HEADER = { "X-Transcendence-Client": "web" };

// ----- Errors -----

export interface ErrorDetail {
	field: string;
	message: string;
}

export class ApiError extends Error {
	readonly status: number;
	readonly code: string;
	readonly details: ErrorDetail[];

	constructor(status: number, code: string, message: string, details: ErrorDetail[] = []) {
		super(message);
		this.name = "ApiError";
		this.status = status;
		this.code = code;
		this.details = details;
	}
}

interface ErrorBody {
	error?: { code?: string; message?: string; details?: ErrorDetail[] };
}

// Services answer { "error": { code, message, details? } }. Traefik's own
// answers (400, 404, 429) have another body: we then fall back to "HTTP_<status>".
async function toApiError(response: Response): Promise<ApiError> {
	let body: ErrorBody = {};
	try {
		body = (await response.json()) as ErrorBody;
	} catch {
		// Not JSON (Traefik page, empty body): keep the defaults below.
	}
	return new ApiError(
		response.status,
		body.error?.code ?? `HTTP_${response.status}`,
		body.error?.message ?? response.statusText,
		body.error?.details ?? [],
	);
}

// ----- Access token (memory only) -----

let accessToken: string | null = null;
let sessionExpiredHandler: (() => void) | null = null;

export function getAccessToken(): string | null {
	return accessToken;
}

export function setAccessToken(token: string | null): void {
	accessToken = token;
}

// AuthContext registers a callback here to switch the UI to "logged out"
// when the refresh token is no longer valid.
export function onSessionExpired(handler: (() => void) | null): void {
	sessionExpiredHandler = handler;
}

// A JWT is "header.payload.signature", each part in base64url. We only read
// "exp" from the payload to know when to refresh; the services verify the
// signature, not us.
function secondsLeft(token: string): number {
	try {
		const payload = token.split(".")[1].replace(/-/g, "+").replace(/_/g, "/");
		const { exp } = JSON.parse(atob(payload)) as { exp?: number };
		return exp === undefined ? 0 : exp - Date.now() / 1000;
	} catch {
		return 0;
	}
}

// ----- Refresh (single-flight) -----

interface TokenResponse {
	access_token: string;
	token_type: "Bearer";
}

// Shared by every caller while a refresh is running. The refresh token is
// rotated on each call, so two parallel refreshes would send the same old
// cookie and the second one would fail.
let refreshInFlight: Promise<string | null> | null = null;

// Returns the new access token, or null if the user is not logged in anymore.
export function refreshAccessToken(): Promise<string | null> {
	refreshInFlight ??= doRefresh().finally(() => {
		refreshInFlight = null;
	});
	return refreshInFlight;
}

async function doRefresh(): Promise<string | null> {
	const response = await fetch(REFRESH_URL, {
		method: "POST",
		headers: CSRF_HEADER,
		credentials: "same-origin",
		signal: AbortSignal.timeout(DEFAULT_TIMEOUT_MS),
	});
	if (response.status === 401) {
		// 401: no cookie, expired or revoked. The session is over.
		setAccessToken(null);
		sessionExpiredHandler?.();
		return null;
	}
    if (!response.ok) {
        throw await toApiError(response);
    }
	const body = (await response.json()) as TokenResponse;
	setAccessToken(body.access_token);
	return body.access_token;
}

// ----- Requests -----

export interface ApiOptions {
	method?: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
	body?: unknown; // sent as JSON
	headers?: Record<string, string>;
	auth?: boolean; // add the Bearer token (default: true)
	signal?: AbortSignal; // to cancel, e.g. when a component unmounts
}

function send(path: string, options: ApiOptions): Promise<Response> {
	const headers: Record<string, string> = { ...options.headers };
	if (options.body !== undefined) {
		headers["Content-Type"] = "application/json";
	}
	if (options.auth !== false && accessToken !== null) {
		headers["Authorization"] = `Bearer ${accessToken}`;
	}
	const timeout = AbortSignal.timeout(DEFAULT_TIMEOUT_MS);

	return fetch(path, {
		method: options.method ?? "GET",
		headers,
		body: options.body === undefined ? undefined : JSON.stringify(options.body),
		credentials: "same-origin",
		signal: options.signal ? AbortSignal.any([options.signal, timeout]) : timeout,
	});
}

// Usage: const me = await apiFetch<Account>("/api/identity/accounts/me");
// Throws ApiError on any non-2xx answer. Returns undefined on 204.
export async function apiFetch<T>(path: string, options: ApiOptions = {}): Promise<T> {
	const auth = options.auth !== false;

	// Proactive refresh: avoid a 401 we can see coming.
	if (auth && accessToken !== null && secondsLeft(accessToken) < REFRESH_MARGIN_SECONDS) {
		await refreshAccessToken();
	}

	let response = await send(path, options);

	// Reactive refresh: the token expired anyway (clock skew, long chain of
	// calls). Refresh once and replay the request once, never more.
	if (auth && response.status === 401) {
		const error = await toApiError(response);
		if (error.code !== "TOKEN_EXPIRED" || (await refreshAccessToken()) === null) {
			throw error;
		}
		response = await send(path, options);
	}

	if (!response.ok) {
		throw await toApiError(response);
	}
	if (response.status === 204) {
		return undefined as T;
	}
	return (await response.json()) as T;
}
