import { formatDate, isExpired } from "@/features/api-keys/format";
import type { ApiKey } from "@/features/api-keys/types";
import { Text } from "@/shared/components/Text";
import { Button } from "@/shared/components/Button";

export function ApiKeyRow({ apiKey, onDelete }: { apiKey: ApiKey; onDelete: () => void }) {
	const expired = isExpired(apiKey.expires_at);

	return (
		// Status and Delete under the key details on a phone, beside them from sm.
		<div className="flex flex-col items-start gap-3 py-2 sm:flex-row sm:items-center sm:justify-between">
			{/* w-full on mobile: truncate needs a fixed width to cut a long name. */}
			<div className="flex w-full min-w-0 flex-col sm:w-auto">
				<Text variant="body" className="font-semibold truncate" title={apiKey.name}>
					{apiKey.name}
				</Text>
				<code className="text-sm">{apiKey.prefix}••••</code>
				<Text variant="body" className="text-info text-sm">
					{apiKey.scopes.join(" + ")} · Expires on {formatDate(apiKey.expires_at)}
				</Text>
			</div>

			<div className="flex shrink-0 items-center gap-3">
				<Text variant={expired ? "error" : "success"}>{expired ? "Expired" : "Active"}</Text>
				<Button variant="chip" type="button" onClick={onDelete}>
					Delete
				</Button>
			</div>
		</div>
	);
}
