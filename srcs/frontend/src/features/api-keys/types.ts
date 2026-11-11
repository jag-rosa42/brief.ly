export const API_KEY_SCOPES = ["read", "write"] as const;
export type ApiKeyScope = (typeof API_KEY_SCOPES)[number];

export function isApiKeyScope(value: string): value is ApiKeyScope {
	return (API_KEY_SCOPES as readonly string[]).includes(value);
}

export interface ApiKey {
	id: string;
	name: string;
	prefix: string;
	scopes: ApiKeyScope[];
	created_at: string;
	expires_at: string;
}

// Réponse du POST : la clé complète n'est renvoyée qu'ici, une seule fois.
export interface CreatedApiKey extends ApiKey {
	key: string;
}

export interface CreateApiKeyPayload {
	name: string;
	scopes: ApiKeyScope[];
}
