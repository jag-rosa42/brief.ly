import { useCallback, useEffect, useState } from "react";
import { createApiKey, deleteApiKey, listApiKeys } from "@/features/api-keys/api";
import type { ApiKey, CreateApiKeyPayload, CreatedApiKey } from "@/features/api-keys/types";

export const MAX_KEYS = 5;
const EXPIRY_MARGIN_MS = 500;

export function useApiKeys() {
	const [keys, setKeys] = useState<ApiKey[]>([]);
	const [loading, setLoading] = useState(true);
	const [loadError, setLoadError] = useState<string | null>(null);
	const [now, setNow] = useState(() => Date.now());

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

	const refreshSilently = useCallback(async () => {
		try {
			setKeys(await listApiKeys());
		} catch {}
	}, []);

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

	useEffect(() => {
		const current = Date.now();
		const nextExpiry = Math.min(
			...keys.map((k) => Date.parse(k.expires_at)).filter((t) => t > current),
		);
		if (!Number.isFinite(nextExpiry)) return;

		const id = setTimeout(
			() => {
				setNow(Date.now());
				void refreshSilently();
			},
			nextExpiry - current + EXPIRY_MARGIN_MS,
		);

		return () => clearTimeout(id);
	}, [keys, refreshSilently]);

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

	const activeKeys = keys.filter((k) => Date.parse(k.expires_at) > now);

	return {
		keys: activeKeys,
		loading,
		loadError,
		reload,
		addKey,
		deleteKey,
		limitReached: activeKeys.length >= MAX_KEYS,
	};
}
