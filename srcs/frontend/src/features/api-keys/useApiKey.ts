import { useEffect, useState } from "react";
import { createApiKey, deleteApiKey, listApiKeys } from "@/features/api-keys/api";
import type { ApiKey, CreateApiKeyPayload, CreatedApiKey } from "@/features/api-keys/types";

export const MAX_KEYS = 5;

export function useApiKeys() {
	const [keys, setKeys] = useState<ApiKey[]>([]);
	const [loading, setLoading] = useState(true);
	const [loadError, setLoadError] = useState<string | null>(null);

	async function reload() {
		setLoading(true);
		setLoadError(null);
		try {
			setKeys(await listApiKeys());
		} catch {
			setLoadError("Unable to load your API keys.");
		} finally {
			setLoading(false);
		}
	}

	useEffect(() => {
		let ignore = false;

		async function fetchKeys() {
			try {
				const items = await listApiKeys();

				if (!ignore) {
					setKeys(items);
				}
			} catch {
				if (!ignore) {
					setLoadError("Unable to load your API keys.");
				}
			} finally {
				if (!ignore) {
					setLoading(false);
				}
			}
		}
		void fetchKeys();
		return () => {
			ignore = true;
		};
	}, []);

	async function addKey(payload: CreateApiKeyPayload): Promise<CreatedApiKey> {
		const created = await createApiKey(payload);
		const item: ApiKey = {
			id: created.id,
			name: created.name,
			prefix: created.prefix,
			scopes: created.scopes,
			created_at: created.created_at,
			expires_at: created.expires_at,
		};
		setKeys((prev) => [item, ...prev]); // les keys les plus récentes d'abord
		return created;
	}

	async function deleteKey(id: string): Promise<void> {
		await deleteApiKey(id);
		setKeys((prev) => prev.filter((k) => k.id !== id));
	}

	return {
		keys,
		loading,
		loadError,
		reload,
		addKey,
		deleteKey,
		limitReached: keys.length >= MAX_KEYS,
	};
}
