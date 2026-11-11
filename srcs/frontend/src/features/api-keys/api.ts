import { apiFetch } from "@/shared/components/api/client";
import type { ApiKey, CreateApiKeyPayload, CreatedApiKey } from "@/features/api-keys/types";

export async function listApiKeys(): Promise<ApiKey[]> {
	const data = await apiFetch<{ items: ApiKey[] }>("/api/identity/api-keys");
	return data.items;
}

export function createApiKey(payload: CreateApiKeyPayload): Promise<CreatedApiKey> {
	return apiFetch<CreatedApiKey>("/api/identity/api-keys", { method: "POST", body: payload });
}

export async function deleteApiKey(id: string): Promise<void> {
	await apiFetch<undefined>(`/api/identity/api-keys/${id}`, { method: "DELETE" });
}
