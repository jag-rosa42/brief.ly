export interface ErrorDetail {
	field: string;
	message: string;
}

interface ErrorBody {
	error?: {
		code?: string;
		message?: string;
		details?: ErrorDetail[];
	};
}

export class ApiError extends Error {
	readonly status: number;
	readonly code: string;
	readonly details: ErrorDetail[];
	// From the Retry-After header of a 429 (the gateway's rate limits): how
	// long to wait before trying again. null when the answer has none.
	readonly retryAfterSeconds: number | null;

	constructor(
		status: number,
		code: string,
		message: string,
		details: ErrorDetail[] = [],
		retryAfterSeconds: number | null = null,
	) {
		super(message);
		this.name = "ApiError";
		this.status = status;
		this.code = code;
		this.details = details;
		this.retryAfterSeconds = retryAfterSeconds;
	}
}

// Retry-After is a number of seconds here: Traefik's rate limiter sends it
// that way (the HTTP-date form is not used).
function retryAfter(response: Response): number | null {
	const value = Number(response.headers.get("Retry-After"));
	return Number.isFinite(value) && value > 0 ? Math.ceil(value) : null;
}

export async function toApiError(response: Response): Promise<ApiError> {
	let body: ErrorBody = {};

	try {
		body = (await response.json()) as ErrorBody;
	} catch {
		// Not our JSON error format (e.g. Traefik's plain-text 404, 429 or
		// 502): fall back to the HTTP status below.
	}

	return new ApiError(
		response.status,
		body.error?.code ?? `HTTP_${response.status}`,
		body.error?.message ?? response.statusText,
		body.error?.details ?? [],
		retryAfter(response),
	);
}
