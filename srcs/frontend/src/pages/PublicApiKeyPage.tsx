import { Fragment, useState } from "react";
import type { ReactNode, SubmitEvent } from "react";
import { useApiKeys, MAX_KEYS, KEY_LIFETIME_MS, formatDate } from "@/utils/useApiKeys";
import { Division } from "@/shared/components/Division";
import { Form } from "@/shared/components/Form";
import { Text } from "@/shared/components/Text";
import { Input } from "@/shared/components/Input";
import { Button } from "@/shared/components/Button";
import { ApiKeyRow } from "@/shared/components/ApiKeyRow";

function validateName(value: string): string | null {
	const name = value.trim();
	if (name.length < 2)
		return "Key name must be at least 2 characters.";
	if (name.length > 30)
		return "Key name must be at most 30 characters.";
	return null;
}

interface ConfirmDialogProps {
	open: boolean;
	message: ReactNode;
	confirmLabel: string;
	onConfirm: () => void;
	onCancel: () => void;
};

function ConfirmDialog({ open, message, confirmLabel, onConfirm, onCancel }: ConfirmDialogProps) {
	if (!open)
		return null;

	return (
		<div
			className="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
			onClick={onCancel}
		>
			<Division variant="featurecard" onClick={(e) => e.stopPropagation()}>
				<Text variant="body">{message}</Text>
				<Button variant="primary" onClick={onCancel}>Cancel</Button>
				<Button variant="secondary" onClick={onConfirm}>{confirmLabel}</Button>
			</Division>
		</div>
	);
}

export function PublicApiKeyPage() {
	const { keys, addKey, deleteKey, limitReached } = useApiKeys();
	const [pendingCreate, setPendingCreate] = useState<{ name: string; expiresAt: number } | null>(null);
	const [creating, setCreating] = useState(false);
	const [name, setName] = useState("");
	const [error, setError] = useState<string | undefined>();
	const [newKey, setNewKey] = useState<{ id: string; secret: string } | null>(null);
	const [copied, setCopied] = useState(false);
	const [pendingDelete, setPendingDelete] = useState<{ id: string; keyName: string } | null>(null);

	function handleCreate(e: SubmitEvent) {
		e.preventDefault();
		const nameError = validateName(name);
		if (nameError) {
			setError(nameError);
			return;
		}
		setPendingCreate({ name: name.trim(), expiresAt: Date.now() + KEY_LIFETIME_MS });
	}

	function confirmCreate() {
		if (pendingCreate) {
			const created = addKey(pendingCreate.name);
			if (created) {
				setNewKey(created);
				setCopied(false);
				setName("");
				setCreating(false);
			}
		}
		setPendingCreate(null);
	}

	async function handleCopy() {
		if (!newKey)
			return;
		try {
			await navigator.clipboard.writeText(newKey.secret);
			setCopied(true);
		} catch {
			setCopied(false);
		}
	}

	function confirmDelete() {
		if (pendingDelete) {
			deleteKey(pendingDelete.id);
			if (newKey?.id === pendingDelete.id)
				setNewKey(null);
		}
		setPendingDelete(null);
	}

	return (
		<Division variant="dashboardpage" className="items-center">
			<Text variant="title" className="mb-10 text-center">API keys</Text>

			<div className="w-full max-w-lg">
				<div className="mb-4 flex items-center justify-between">
					<Text variant="subheading">Manage your public API keys</Text>
					<Text variant="body" className="text-info">{keys.length} / {MAX_KEYS}</Text>
					<Button
						variant="secondary"
						disabled={limitReached || creating}
						onClick={() => { setCreating(true); setNewKey(null); }}
					>
						+
					</Button>
				</div>

				{creating && (
					<Division variant="featurecard" className="mb-4 shadow-sm">
						<Form
							onSubmit={handleCreate}
							actions={
								<div className="flex flex-col gap-3 w-full">
									<Button type="submit" variant="secondary" className="w-full">Create</Button>
									<Button
										type="button"
										variant="primary"
										className="w-full"
										onClick={() => { setCreating(false); setName(""); setError(undefined); }}
									>
										Cancel
									</Button>
								</div>
							}
						>
							<Input
								variant="main"
								label="Key name"
								name="keyName"
								value={name}
								error={error}
								onChange={(e) => { setName(e.target.value); setError(undefined); }}
							/>
							<Text variant="body" className="text-info">
								This key will expire in 48 hours.
							</Text>
						</Form>
					</Division>
				)}

				<Division variant="featurecard" className="shadow-sm">
					{keys.length === 0 ? (
						<Text variant="body">No API key yet.</Text>
					) : (
						keys.map((k) => (
							<Fragment key={k.id}>
								<ApiKeyRow
									apiKey={k}
									onDelete={() => setPendingDelete({ id: k.id, keyName: k.name })}
								/>

								{newKey?.id === k.id && (
									<div className="my-3 rounded-lg border border-green-600/40 bg-green-600/10 p-3">
										<Text variant="body">
											Copy your API key now. You won't be able to see it again.
										</Text>
										<div className="mt-2 flex items-center gap-2">
											<code className="flex-1 break-all rounded border px-3 py-2 text-sm">
												{newKey.secret}
											</code>
											<Button variant="secondary" onClick={() => { void handleCopy(); }}>
												{copied ? "Copied ✓" : "Copy"}
											</Button>
										</div>
									</div>
								)}
							</Fragment>
						))
					)}
				</Division>
			</div>

			<ConfirmDialog
				open={pendingDelete !== null}
				message={`Delete "${pendingDelete?.keyName}" ?`}
				confirmLabel="Delete"
				onConfirm={confirmDelete}
				onCancel={() => setPendingDelete(null)}
			/>
			<ConfirmDialog
				open={pendingCreate !== null}
				message={
					<>
						Your new API key <strong>{pendingCreate?.name}</strong> will be ready for use
						immediately. It will expire on{" "}
						<strong>{pendingCreate ? formatDate(pendingCreate.expiresAt) : ""}</strong>.
					</>
				}
				confirmLabel="Generate key"
				onConfirm={confirmCreate}
				onCancel={() => setPendingCreate(null)}
			/>
		</Division>
	);
}