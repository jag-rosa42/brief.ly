import { session } from "@/shared/components/api/session";

const DEFAULT_TIMEOUT_MS = 10_000;

export interface ApiOptions {
	method?: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
	body?: unknown; // sent as JSON
	headers?: Record<string, string>;
	auth?: boolean; //add the Bearer token
	signal?: AbortSignal;
}

export function send(path: string, options: ApiOptions = {}): Promise<Response> {
	const headers: Record<string, string> = { ...options.headers };
	if (options.body !== undefined) {
		headers["Content-Type"] = "application/json";
	}
	const token = session.getAccessToken();
	if (options.auth !== false && token !== null) {
		headers.Authorization = `Bearer ${token}`;
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