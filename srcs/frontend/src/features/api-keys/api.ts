import { apiFetch } from "@/shared/components/api/client";
/*import type { ApiKey, CreateApiKeyPayload, CreatedApiKey } from "@/features/api-keys/types";

export async function listApiKeys(): Promise<ApiKey[]> {
	const data = await apiFetch<{ items: ApiKey[] }>("/api/identity/api-keys");
	return data.items;
}

export function createApiKey(payload: CreateApiKeyPayload): Promise<CreatedApiKey> {
	return apiFetch<CreatedApiKey>("/api/identity/api-keys", { method: "POST", body: payload });
}

export async function deleteApiKey(id: string): Promise<void> {
	await apiFetch<undefined>(`/api/identity/api-keys/${id}`, { method: "DELETE" });
}*/

import type { ApiKey, CreateApiKeyPayload, CreatedApiKey } from "@/features/api-keys/types";

// MODE TEST
const MOCK_API = true;

const delay = (ms = 500) => new Promise((resolve) => setTimeout(resolve, ms));

const mockKeys: ApiKey[] = [
	{
		id: "1",
		name: "My personal script",
		prefix: "tr_8f3k",
		scopes: ["read"],
		created_at: new Date().toISOString(),
		expires_at: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(),
	},
	{
		id: "2",
		name: "Website integration",
		prefix: "tr_2a9x",
		scopes: ["read", "write"],
		created_at: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
		expires_at: new Date(Date.now() - 1000).toISOString(),
	},
];

export async function listApiKeys(): Promise<ApiKey[]> {
	if (MOCK_API) {
		await delay();
		return [...mockKeys];
	}

	const data = await apiFetch<{ items: ApiKey[] }>("/api/identity/api-keys");
	return data.items;
}

export async function createApiKey(payload: CreateApiKeyPayload): Promise<CreatedApiKey> {
	if (MOCK_API) {
		await delay();

		const now = new Date();

		const created: CreatedApiKey = {
			id: crypto.randomUUID(),
			name: payload.name,
			prefix: "tr_mock",
			scopes: payload.scopes,
			created_at: now.toISOString(),
			expires_at: new Date(now.getTime() + 48 * 60 * 60 * 1000).toISOString(),
			key: `tr_mock_${crypto.randomUUID()}`,
		};

		mockKeys.unshift({
			id: created.id,
			name: created.name,
			prefix: created.prefix,
			scopes: created.scopes,
			created_at: created.created_at,
			expires_at: created.expires_at,
		});

		return created;
	}

	return apiFetch<CreatedApiKey>("/api/identity/api-keys", {
		method: "POST",
		body: payload,
	});
}

export async function deleteApiKey(id: string): Promise<void> {
	if (MOCK_API) {
		await delay();

		const index = mockKeys.findIndex((key) => key.id === id);

		if (index !== -1) mockKeys.splice(index, 1);

		return;
	}

	await apiFetch<undefined>(`/api/identity/api-keys/${id}`, {
		method: "DELETE",
	});
}
