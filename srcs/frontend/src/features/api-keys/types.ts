export type ApiKeyScope = "read" | "write";

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
