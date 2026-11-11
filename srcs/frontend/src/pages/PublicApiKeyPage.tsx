import { useCallback, useState } from "react";
import type { ReactNode, SubmitEvent } from "react";
import { useApiKeys, MAX_KEYS } from "@/features/api-keys/useApiKey";
import { mapApiKeyError } from "@/features/api-keys/error";
import type { ApiKeyScope } from "@/features/api-keys/types";
import { isApiKeyScope } from "@/features/api-keys/types";
import { Division } from "@/shared/components/Division";
import { Form } from "@/shared/components/Form";
import { Text } from "@/shared/components/Text";
import { Input } from "@/shared/components/Input";
import { Button } from "@/shared/components/Button";
import { FilterChip } from "@/shared/components/FilterChip";
import { ApiKeyRow } from "@/shared/components/ApiKeyRow";
import { ApiError } from "@/shared/components/api/client";
import { Notification } from "@/shared/components/Notification";
import type { NotificationVariant } from "@/shared/components/notificationVariants";

const NAME_MIN = 1;
const NAME_MAX = 50;

const SCOPE_OPTIONS: { value: ApiKeyScope; label: string; description: string }[] = [
	{ value: "read", label: "Read", description: "View your data" },
	{ value: "write", label: "Write", description: "Create and modify data" },
];

function validateName(value: string): string | null {
	const length = value.trim().length;
	if (length < NAME_MIN) return `Key name must be at least ${NAME_MIN} character.`;
	if (length > NAME_MAX) return `Key name must be at most ${NAME_MAX} characters.`;
	return null;
}

interface ConfirmDialogProps {
	open: boolean;
	message: ReactNode;
	confirmLabel: string;
	ariaLabel: string;
	role?: "dialog" | "alertdialog";
	busy?: boolean;
	onConfirm: () => void;
	onCancel: () => void;
}

function ConfirmDialog({
	open,
	message,
	confirmLabel,
	ariaLabel,
	role = "dialog",
	busy = false,
	onConfirm,
	onCancel,
}: ConfirmDialogProps) {
	if (!open) return null;

	return (
		<div
			role={role}
			aria-modal="true"
			aria-label={ariaLabel}
			className="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
			onClick={onCancel}
		>
			<Division variant="featurecard" onClick={(e) => e.stopPropagation()}>
				<Text variant="body">{message}</Text>
				<Button variant="primary" onClick={onCancel} disabled={busy}>
					Cancel
				</Button>
				<Button variant="secondary" onClick={onConfirm} disabled={busy}>
					{busy ? "Please wait..." : confirmLabel}
				</Button>
			</Division>
		</div>
	);
}

interface NewKeyDialogProps {
	secret: string;
	expiresAt: string;
	copyFailed: boolean;
	onCopyAndClose: () => void;
	onClose: () => void;
}

function NewKeyDialog({
	secret,
	expiresAt,
	copyFailed,
	onCopyAndClose,
	onClose,
}: NewKeyDialogProps) {
	return (
		<div
			className="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
			role="dialog"
			aria-modal="true"
			aria-labelledby="new-key-title"
		>
			<Division variant="featurecard">
				<Text variant="subheading" id="new-key-title">
					Your new API key
				</Text>
				<Text variant="body">Copy it now. You won't be able to see it again.</Text>
				<code
					className="break-all rounded border px-3 py-2 text-sm"
					onClick={(e) => window.getSelection()?.selectAllChildren(e.currentTarget)}
				>
					{secret}
				</code>
				<Text variant="body" className="text-info">
					Expires on {new Date(expiresAt).toLocaleString()}
				</Text>
				<Button variant="secondary" onClick={onCopyAndClose}>
					Copy and close
				</Button>
				{copyFailed && (
					<>
						<Text variant="error" role="alert">
							Copy failed. Select the key above and copy it manually.
						</Text>
						<Button variant="primary" onClick={onClose}>
							Close anyway
						</Button>
					</>
				)}
			</Division>
		</div>
	);
}

export function PublicApiKeyPage() {
	const { keys, loading, loadError, reload, addKey, deleteKey, limitReached } = useApiKeys();

	const [creating, setCreating] = useState(false);
	const [name, setName] = useState("");
	const [scopes, setScopes] = useState<ApiKeyScope[]>(["read"]);
	const [fieldError, setFieldError] = useState<string | undefined>();
	const [pendingCreate, setPendingCreate] = useState<{
		name: string;
		scopes: ApiKeyScope[];
	} | null>(null);
	const [pendingDelete, setPendingDelete] = useState<{ id: string; keyName: string } | null>(null);
	const [busy, setBusy] = useState(false);
	const [newKey, setNewKey] = useState<{ id: string; secret: string; expiresAt: string } | null>(
		null,
	);
	const [copyFailed, setCopyFailed] = useState(false);
	const [notification, setNotification] = useState<{
		id: number;
		message: string;
		variant: NotificationVariant;
	} | null>(null);

	const closeNotification = useCallback(() => setNotification(null), []);

	function notify(message: string, variant: NotificationVariant) {
		setNotification({ id: Date.now(), message, variant });
	}

	function toggleScope(value: string) {
		if (!isApiKeyScope(value)) return;
		setScopes((prev) => {
			if (!prev.includes(value)) return [...prev, value];
			if (prev.length === 1) return prev;
			return prev.filter((s) => s !== value);
		});
	}

	function resetForm() {
		setCreating(false);
		setName("");
		setScopes(["read"]);
		setFieldError(undefined);
	}

	function handleCreate(e: SubmitEvent) {
		e.preventDefault();
		const nameError = validateName(name);
		if (nameError) {
			setFieldError(nameError);
			return;
		}
		if (scopes.length === 0) {
			setFieldError("Pick at least one permission.");
			return;
		}
		setPendingCreate({ name: name.trim(), scopes });
	}

	async function confirmCreate() {
		if (!pendingCreate || busy) return;
		setBusy(true);
		try {
			const created = await addKey(pendingCreate);
			setNewKey({ id: created.id, secret: created.key, expiresAt: created.expires_at });
			setCopyFailed(false);
			resetForm();
		} catch (e) {
			notify(mapApiKeyError(e), "error");
			if (e instanceof ApiError && e.code === "API_KEY_LIMIT_REACHED") {
				void reload();
			}
		} finally {
			setPendingCreate(null);
			setBusy(false);
		}
	}

	async function confirmDelete() {
		if (!pendingDelete || busy) return;
		setBusy(true);
		try {
			await deleteKey(pendingDelete.id);
			notify("API key deleted.", "success");
		} catch (e) {
			notify(mapApiKeyError(e), "error");
		} finally {
			setPendingDelete(null);
			setBusy(false);
		}
	}

	async function handleCopy(): Promise<boolean> {
		if (!newKey) return false;
		try {
			await navigator.clipboard.writeText(newKey.secret);
			return true;
		} catch {
			return false;
		}
	}

	async function handleCopyAndClose() {
		const ok = await handleCopy();
		if (ok) {
			setNewKey(null);
			setCopyFailed(false);
			notify("API key created.", "success");
		} else {
			setCopyFailed(true);
		}
	}

	return (
		<Division variant="dashboardpage" className="items-center">
			<Text variant="title" className="mb-10 text-center">
				API keys
			</Text>

			<div className="w-full max-w-lg">
				<div className="mb-4 flex items-center justify-between">
					<Text variant="subheading">Manage your public API keys</Text>
					{!loading && !loadError && (
						<Text variant="body" className="text-info">
							{keys.length} / {MAX_KEYS}
						</Text>
					)}
					<Button
						variant="secondary"
						disabled={loading || loadError !== null || limitReached || creating}
						onClick={() => {
							setCreating(true);
						}}
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
									<Button type="submit" variant="secondary" className="w-full">
										Create
									</Button>
									<Button type="button" variant="primary" className="w-full" onClick={resetForm}>
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
								error={fieldError}
								onChange={(e) => {
									setName(e.target.value);
									setFieldError(undefined);
								}}
							/>
							<div className="flex flex-col gap-2">
								<Text variant="body" className="font-semibold">
									Permissions
								</Text>
								<div className="flex gap-2">
									{SCOPE_OPTIONS.map((opt) => (
										<FilterChip
											key={opt.value}
											options={opt}
											selected={scopes.includes(opt.value)}
											onToggle={toggleScope}
										/>
									))}
								</div>
								<Text variant="body" className="text-info text-sm">
									Select at least one. You can combine both.{" "}
									{SCOPE_OPTIONS.filter((option) => scopes.includes(option.value))
										.map((option) => `${option.label}: ${option.description}.`)
										.join(" ")}
								</Text>
							</div>
						</Form>
					</Division>
				)}

				<Division variant="featurecard" className="shadow-sm">
					{loading && <Text variant="body">Loading API keys...</Text>}

					{!loading && loadError && (
						<div className="flex flex-col items-center gap-2">
							<Text variant="error" role="alert">
								{loadError}
							</Text>
							<Button type="button" variant="secondary" onClick={() => void reload()}>
								Retry
							</Button>
						</div>
					)}

					{!loading && !loadError && keys.length === 0 && (
						<Text variant="body">No API key yet.</Text>
					)}

					{!loading &&
						!loadError &&
						keys.map((k) => (
							<Division key={k.id} variant="stack">
								<ApiKeyRow
									apiKey={k}
									onDelete={() => setPendingDelete({ id: k.id, keyName: k.name })}
								/>
							</Division>
						))}
				</Division>
			</div>

			<ConfirmDialog
				open={pendingDelete !== null}
				role="alertdialog"
				ariaLabel="Delete API key"
				message={`Delete "${pendingDelete?.keyName ?? ""}" ?`}
				confirmLabel="Delete"
				busy={busy}
				onConfirm={() => void confirmDelete()}
				onCancel={() => setPendingDelete(null)}
			/>
			<ConfirmDialog
				open={pendingCreate !== null}
				ariaLabel="Create API key"
				message={
					<>
						Your new API key <strong>{pendingCreate?.name}</strong> (
						{pendingCreate?.scopes.join(" + ")}) will be ready for use immediately. It will expire
						48 hours after creation.
					</>
				}
				aria-label="Create API key"
				confirmLabel="Generate key"
				busy={busy}
				onConfirm={() => void confirmCreate()}
				onCancel={() => setPendingCreate(null)}
			/>
			{newKey && (
				<NewKeyDialog
					secret={newKey.secret}
					expiresAt={newKey.expiresAt}
					copyFailed={copyFailed}
					onCopyAndClose={() => void handleCopyAndClose()}
					onClose={() => {
						setNewKey(null);
						setCopyFailed(false);
						notify("API key created.", "success");
					}}
				/>
			)}
			{notification && (
				<Notification
					key={notification.id}
					message={notification.message}
					variant={notification.variant}
					onClose={closeNotification}
				/>
			)}
		</Division>
	);
}
