import { toApiError } from "@/shared/components/api/error";

const DEFAULT_TIMEOUT_MS = 10_000;
const SESSION_HINT_KEY = "hasSession";

export const CSRF_HEADER = {
	"X-Transcendence-Client": "web",
};

interface TokenResponse {
	access_token: string;
	token_type: "Bearer";
}

export class Session {
	private accessToken: string | null = null;
	private refreshInFlight: Promise<string | null> | null = null;
	private readonly expiredListeners = new Set<() => void>();

	private hasSessionHint(): boolean {
		try {
			return localStorage.getItem(SESSION_HINT_KEY) === "1";
		} catch {
			return false;
		}
	}

	private setSessionHint(): void {
		try {
			localStorage.setItem(SESSION_HINT_KEY, "1");
		} catch {
			// Ignore unavailable localStorage: the session still works on memory with refresh token.
		}
	}

	private clearSessionHint(): void {
		try {
			localStorage.removeItem(SESSION_HINT_KEY);
		} catch {
			// If localStorage is unavailable, the session is kept active with a refresh call.
		}
	}

	getAccessToken(): string | null {
		return this.accessToken;
	}

	setAccessToken(token: string | null): void {
		this.accessToken = token;

		if (token)
			this.setSessionHint();
		else
			this.clearSessionHint();
	}

	onExpired(listener: () => void): () => void {
		this.expiredListeners.add(listener);

		return () => {
			this.expiredListeners.delete(listener);
		};
	}

	refresh(): Promise<string | null> {
		this.refreshInFlight ??= this.doRefresh().finally(() => {
			this.refreshInFlight = null;
		});

		return this.refreshInFlight;
	}

	private async doRefresh(): Promise<string | null> {
		if (!this.hasSessionHint()) {
			this.setAccessToken(null);
			return null;
		}

		const response = await fetch("/api/identity/auth/refresh", {
			method: "POST",
			headers: CSRF_HEADER,
			credentials: "same-origin",
			signal: AbortSignal.timeout(DEFAULT_TIMEOUT_MS),
		});

		if (response.status === 401) {
			this.setAccessToken(null);
			this.expiredListeners.forEach((listener) => listener());
			return null;
		}

		if (!response.ok)
			throw await toApiError(response);

		const body = (await response.json()) as TokenResponse;

		this.setAccessToken(body.access_token);

		return body.access_token;
	}
}

export const session = new Session();
