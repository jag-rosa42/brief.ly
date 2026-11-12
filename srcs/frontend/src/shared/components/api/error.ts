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

	constructor(status: number, code: string, message: string, details: ErrorDetail[] = []) {
		super(message);
		this.name = "ApiError";
		this.status = status;
		this.code = code;
		this.details = details;
	}
}

export async function toApiError(response: Response): Promise<ApiError> {
	let body: ErrorBody = {};

	try {
		body = (await response.json()) as ErrorBody;
	} catch {
		// Not our JSON error format (e.g. Traefik's plain-text 404 or 502):
		// fall back to the HTTP status below.
	}

	return new ApiError(
		response.status,
		body.error?.code ?? `HTTP_${response.status}`,
		body.error?.message ?? response.statusText,
		body.error?.details ?? [],
	);
}
