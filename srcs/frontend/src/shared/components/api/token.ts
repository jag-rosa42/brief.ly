const REFRESH_MARGIN_SECONDS = 60;

export function isTokenNearExpiry(token: string): boolean {
	try {
		const payload = token
			.split(".")[1]
			.replace(/-/g, "+")
			.replace(/_/g, "/");

		const { exp } = JSON.parse(atob(payload)) as {
			exp?: number;
		};

		if (exp === undefined)
			return true;

		return exp - Date.now() / 1000 < REFRESH_MARGIN_SECONDS;
	} catch {
		return true;
	}
}