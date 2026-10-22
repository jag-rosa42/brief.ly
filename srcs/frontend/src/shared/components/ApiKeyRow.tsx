import { getStatus, formatDate } from "@/utils/useApiKeys";
import type { ApiKey } from "@/utils/useApiKeys";
import { Text } from "@/shared/components/Text";
import { Button } from "@/shared/components/Button";

export function ApiKeyRow({ apiKey, onDelete }: { apiKey: ApiKey; onDelete: () => void }) {
	const status = getStatus(apiKey);

	return (
		<div className="flex items-center justify-between gap-3 py-2">
			<div className="flex flex-col">
				<Text variant="body" className="font-semibold">{apiKey.name}</Text>
				<code className="text-sm">••••{apiKey.lastChars}</code>
				<Text variant="body" className="text-info text-sm">
					Expires on {formatDate(apiKey.expires)}
				</Text>
			</div>

			<div className="flex items-center gap-3">
				<Text variant={status === "active" ? "success" : "error"}>
					{status === "active" ? "Active" : "Revoked"}
				</Text>
				<Button variant="chip" type="button" onClick={onDelete}>
					Delete
				</Button>
			</div>
		</div>
	);
}