import { toApiError } from "@/shared/components/api/error";
import { send, type ApiOptions } from "@/shared/components/api/request";
import { session } from "@/shared/components/api/session";
import { isTokenNearExpiry } from "@/shared/components/api/token";

export { ApiError, type ErrorDetail } from "@/shared/components/api/error";
export { CSRF_HEADER } from "@/shared/components/api/session";
export { session } from "@/shared/components/api/session";
export type { ApiOptions } from "@/shared/components/api/request";

//There is no refresh automatic if the user stays on a logged page for a long time. However,
// the token is checked whenever a request is made so that the user's status (connected/non connected)
// is updated at that moment.

// Send the request with the session's token, refreshing it when needed.
// Returns the response once it is OK; throws an ApiError otherwise.
async function sendWithSession(path: string, options: ApiOptions): Promise<Response> {
	const auth = options.auth !== false;
	const token = session.getAccessToken();

	// Proactive refresh to counter the 401 error
	if (auth && token !== null && isTokenNearExpiry(token)) {
		await session.refresh();
	}
	let response = await send(path, options);

	// Reactive refresh: retry once if the token expired.
	if (auth && response.status === 401) {
		const error = await toApiError(response);

		if (error.code !== "TOKEN_EXPIRED" || (await session.refresh()) === null) throw error;
		response = await send(path, options);
	}
	if (!response.ok) throw await toApiError(response);

	return response;
}

export async function apiFetch<T>(path: string, options: ApiOptions = {}): Promise<T> {
	const response = await sendWithSession(path, options);

	if (response.status === 204) {
		return undefined as T;
	}

	return (await response.json()) as T;
}

// For an answer that arrives piece by piece (text/event-stream): returns the
// response as soon as its status is OK, without reading the body, so the
// caller can read response.body while it arrives. Errors before the stream
// (401, 422, 429, 503...) throw an ApiError, like apiFetch.
export function apiStream(path: string, options: ApiOptions = {}): Promise<Response> {
	return sendWithSession(path, options);
}
