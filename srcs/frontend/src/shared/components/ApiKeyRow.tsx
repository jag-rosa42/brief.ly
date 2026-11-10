import { formatDate, isExpired } from "@/features/api-keys/format";
import type { ApiKey } from "@/features/api-keys/types";
import { Text } from "@/shared/components/Text";
import { Button } from "@/shared/components/Button";

export function ApiKeyRow({ apiKey, onDelete }: { apiKey: ApiKey; onDelete: () => void }) {
	const expired = isExpired(apiKey.expires_at);

	return (
		<div className="flex items-center justify-between gap-3 py-2">
			<div className="flex flex-col min-w-0">
				<Text variant="body" className="font-semibold truncate" title={apiKey.name}>
					{apiKey.name}
				</Text>
				<code className="text-sm">{apiKey.prefix}••••</code>
				<Text variant="body" className="text-info text-sm">
					{apiKey.scopes.join(" + ")} · Expires on {formatDate(apiKey.expires_at)}
				</Text>
			</div>

			<div className="flex items-center gap-3">
				<Text variant={expired ? "error" : "success"}>{expired ? "Expired" : "Active"}</Text>
				<Button variant="chip" type="button" onClick={onDelete}>
					Delete
				</Button>
			</div>
		</div>
	);
}
