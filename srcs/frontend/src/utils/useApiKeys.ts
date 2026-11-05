import { useState } from "react";

export type ApiKeyStatus = "active" | "revoked";

export interface ApiKey {
	id: string;
	name: string;
	lastChars: string;
	expires: number;
	status: ApiKeyStatus;
}

export const MAX_KEYS = 5;
export const KEY_LIFETIME_MS = 48 * 60 * 60 * 1000;

export function formatDate(timestamp: number): string {
	return new Date(timestamp).toLocaleString("en-GB", {
		day: "2-digit",
		month: "2-digit",
		year: "numeric",
		hour: "2-digit",
		minute: "2-digit",
	});
}

const mockKeys: ApiKey[] = [
	{
		id: "1",
		name: "My key",
		lastChars: "a1b2",
		expires: Date.now() + KEY_LIFETIME_MS,
		status: "active",
	},
	{
		id: "2",
		name: "Key test",
		lastChars: "c3d4",
		expires: Date.now() + KEY_LIFETIME_MS,
		status: "revoked",
	},
	{ id: "3", name: "Key 3", lastChars: "e5f6", expires: Date.now() - 1000, status: "active" },
];

export function getStatus(apiKey: ApiKey): ApiKeyStatus {
	if (apiKey.status === "revoked") return "revoked";

	if (apiKey.expires < Date.now()) return "revoked";

	return "active";
}

export function useApiKeys() {
	const [keys, setKeys] = useState<ApiKey[]>(mockKeys);

	function addKey(name: string): { id: string; secret: string } | null {
		if (keys.length >= MAX_KEYS) return null;
		const secret = Math.random().toString(36).slice(2, 18);
		const id = crypto.randomUUID();
		setKeys((prev) => [
			...prev,
			{
				id,
				name,
				lastChars: secret.slice(-4),
				expires: Date.now() + KEY_LIFETIME_MS,
				status: "active",
			},
		]);
		return { id, secret };
	}
	function deleteKey(id: string) {
		setKeys((prev) => prev.filter((k) => k.id !== id));
	}

	return { keys, addKey, deleteKey, limitReached: keys.length >= MAX_KEYS };
}
