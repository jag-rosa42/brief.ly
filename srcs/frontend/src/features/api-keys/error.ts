import { ApiError } from "@/shared/components/api/client";
import { MAX_KEYS } from "@/features/api-keys/useApiKey";

export function mapApiKeyError(err: unknown): string {
	if (!(err instanceof ApiError)) {
		return "Unable to reach the server. Check your connection and try again.";
	}
	if (err.code === "API_KEY_LIMIT_REACHED") {
		return `You already have ${MAX_KEYS} active keys. Delete one before creating another.`;
	}
	if (err.status === 422) {
		const first = err.details[0];
		return first ? first.message : "Some information is invalid. Please check your entries.";
	}
	if (err.status === 502 || err.status === 503 || err.status === 504) {
		return "Service temporarily unavailable. Please try again later.";
	}
	return "Something went wrong. Please try again.";
}
