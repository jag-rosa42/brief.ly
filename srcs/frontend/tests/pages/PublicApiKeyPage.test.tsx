import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, expect, test, vi } from "vitest";
import { AuthContext, type AuthContextValue } from "@/app/AuthContextDefinition";
import { ProfileProvider } from "@/app/ProfileContext";
import { AppRouter } from "@/app/router";
import { useApiKeys } from "@/features/api-keys/useApiKey";
import { PublicApiKeyPage } from "@/pages/PublicApiKeyPage";
import { ApiError } from "@/shared/components/api/client";

// Each test decides what the hook answers. MAX_KEYS is kept as a plain constant.
vi.mock("@/features/api-keys/useApiKey", () => ({
	useApiKeys: vi.fn(),
	MAX_KEYS: 5,
}));

const SECRET = "tr_8f3k_full_secret_key_shown_only_once";

const FIRST = {
	id: "550e8400-e29b-41d4-a716-446655440001",
	name: "My script",
	prefix: "tr_8f3k",
	scopes: ["read"],
	created_at: new Date(Date.now() - 60_000).toISOString(),
	expires_at: new Date(Date.now() + 47 * 3_600_000).toISOString(),
};

const SECOND = {
	id: "550e8400-e29b-41d4-a716-446655440002",
	name: "Website integration",
	prefix: "tr_2a9x",
	scopes: ["read", "write"],
	created_at: new Date(Date.now() - 120_000).toISOString(),
	expires_at: new Date(Date.now() + 46 * 3_600_000).toISOString(),
};

const CREATED = {
	id: "550e8400-e29b-41d4-a716-446655440003",
	name: "New key",
	prefix: "tr_8f3k",
	scopes: ["read"],
	created_at: new Date().toISOString(),
	expires_at: new Date(Date.now() + 48 * 3_600_000).toISOString(),
	key: SECRET,
};

// Builds the value returned by useApiKeys. Override only what the test needs.
function mockHook(overrides: Record<string, unknown> = {}) {
	const value = {
		keys: [],
		loading: false,
		loadError: null,
		reload: vi.fn(),
		addKey: vi.fn(),
		deleteKey: vi.fn(),
		limitReached: false,
		...overrides,
	};
	vi.mocked(useApiKeys).mockReturnValue(value);
	return value;
}

function renderPage() {
	render(<PublicApiKeyPage />);
}

function clickPlus() {
	fireEvent.click(screen.getByRole("button", { name: /^\+$|create api key/i }));
}

function fillName(value: string) {
	fireEvent.change(screen.getByLabelText("Key name"), { target: { value } });
}

// Opens the form, fills the name and clicks Create.
function submitForm(name = "New key") {
	clickPlus();
	fillName(name);
	fireEvent.click(screen.getByRole("button", { name: "Create" }));
}

// Goes through the whole flow until the "Your new API key" dialog is shown.
async function createKeyUntilDialog() {
	const hook = mockHook({ addKey: vi.fn().mockResolvedValue(CREATED) });
	renderPage();
	submitForm();
	fireEvent.click(screen.getByRole("button", { name: "Generate key" }));
	const secret = await screen.findByText(SECRET);
	const dialog = secret.closest<HTMLElement>('[role="dialog"]')!;
	return { hook, dialog };
}

function mockClipboard(writeText: () => Promise<void>) {
	Object.defineProperty(navigator, "clipboard", {
		value: { writeText },
		configurable: true,
	});
}

beforeEach(() => {
	mockClipboard(vi.fn().mockResolvedValue(undefined));
});

afterEach(() => {
	vi.mocked(useApiKeys).mockReset();
});

// ---------------------------------------------------------------------------
// List
// ---------------------------------------------------------------------------

test("shows a loading message while the keys are loading", () => {
	mockHook({ loading: true });

	renderPage();

	expect(screen.getByText("Loading API keys...")).toBeInTheDocument();
});

test("shows the empty state and a 0 / 5 counter when there is no key", () => {
	mockHook({ keys: [] });

	renderPage();

	expect(screen.getByText("No API key yet.")).toBeInTheDocument();
	expect(screen.getByText("0 / 5")).toBeInTheDocument();
});

test("links to the public API documentation in a new tab", () => {
	mockHook();

	renderPage();

	const link = screen.getByRole("link", { name: /public api documentation/i });
	expect(link).toHaveAttribute("href", "/public/v1/docs");
	expect(link).toHaveAttribute("target", "_blank");
	expect(link).toHaveAttribute("rel", "noopener noreferrer");
});

test("shows the keys and the counter", () => {
	mockHook({ keys: [FIRST, SECOND] });

	renderPage();

	expect(screen.getByText(FIRST.name)).toBeInTheDocument();
	expect(screen.getByText(SECOND.name)).toBeInTheDocument();
	expect(screen.getByText("2 / 5")).toBeInTheDocument();
});

test("never shows a full key in the list", () => {
	mockHook({ keys: [FIRST] });

	renderPage();

	expect(screen.queryByText(SECRET)).not.toBeInTheDocument();
});

test("shows an error and a Retry button when the keys cannot be loaded", () => {
	const hook = mockHook({ loadError: "Something went wrong. Please try again." });

	renderPage();
	fireEvent.click(screen.getByRole("button", { name: "Retry" }));

	expect(screen.getByRole("alert")).toHaveTextContent("Something went wrong. Please try again.");
	expect(hook.reload).toHaveBeenCalledTimes(1);
	expect(screen.queryByText(/\/ 5/)).not.toBeInTheDocument();
});

test("disables the + button when the limit is reached", () => {
	mockHook({ keys: [FIRST], limitReached: true });

	renderPage();

	expect(screen.getByRole("button", { name: /^\+$|create api key/i })).toBeDisabled();
});

// ---------------------------------------------------------------------------
// Form validation
// ---------------------------------------------------------------------------

test("opens the creation form with Read selected by default", () => {
	mockHook();

	renderPage();
	clickPlus();

	expect(screen.getByLabelText("Key name")).toBeInTheDocument();
	expect(screen.getByRole("button", { name: "Read" })).toBeInTheDocument();
	expect(screen.getByRole("button", { name: "Write" })).toBeInTheDocument();
});

test("closes the form and empties it when clicking Cancel", () => {
	mockHook();

	renderPage();
	clickPlus();
	fillName("Something");
	fireEvent.click(screen.getByRole("button", { name: "Cancel" }));

	expect(screen.queryByLabelText("Key name")).not.toBeInTheDocument();

	clickPlus();
	expect(screen.getByLabelText("Key name")).toHaveValue("");
});

test("rejects an empty name without sending anything", () => {
	const hook = mockHook();

	renderPage();
	submitForm("");

	expect(screen.getByText("Key name must be at least 1 character.")).toBeInTheDocument();
	expect(screen.queryByRole("button", { name: "Generate key" })).not.toBeInTheDocument();
	expect(hook.addKey).not.toHaveBeenCalled();
});

test("rejects a name made only of spaces", () => {
	const hook = mockHook();

	renderPage();
	submitForm("     ");

	expect(screen.getByText("Key name must be at least 1 character.")).toBeInTheDocument();
	expect(hook.addKey).not.toHaveBeenCalled();
});

test("rejects a name longer than 50 characters", () => {
	const hook = mockHook();

	renderPage();
	submitForm("a".repeat(51));

	expect(screen.getByText("Key name must be at most 50 characters.")).toBeInTheDocument();
	expect(hook.addKey).not.toHaveBeenCalled();
});

test("accepts a name of exactly 50 characters", () => {
	mockHook();

	renderPage();
	submitForm("a".repeat(50));

	expect(screen.getByRole("button", { name: "Generate key" })).toBeInTheDocument();
});

test("keeps at least one permission selected", () => {
	mockHook();

	renderPage();
	clickPlus();
	// Read is the only selected permission: clicking it must change nothing.
	fireEvent.click(screen.getByRole("button", { name: "Read" }));
	fillName("New key");
	fireEvent.click(screen.getByRole("button", { name: "Create" }));

	expect(screen.getByText(/will be ready for use immediately/)).toHaveTextContent("(read)");
});

test("can combine read and write", () => {
	mockHook();

	renderPage();
	clickPlus();
	fireEvent.click(screen.getByRole("button", { name: "Write" }));
	fillName("New key");
	fireEvent.click(screen.getByRole("button", { name: "Create" }));

	expect(screen.getByText(/will be ready for use immediately/)).toHaveTextContent("(read + write)");
});

// ---------------------------------------------------------------------------
// Creation flow
// ---------------------------------------------------------------------------

test("asks for a confirmation that mentions the 48 hour expiration", () => {
	const hook = mockHook();

	renderPage();
	submitForm("New key");

	expect(screen.getByText(/It will expire 48 hours after creation/)).toBeInTheDocument();
	expect(hook.addKey).not.toHaveBeenCalled();
});

test("does not create anything when the confirmation is cancelled", () => {
	const hook = mockHook();

	renderPage();
	submitForm("New key");
	// Two Cancel buttons exist (form + dialog): the dialog is rendered last.
	fireEvent.click(screen.getAllByRole("button", { name: "Cancel" }).at(-1)!);

	expect(hook.addKey).not.toHaveBeenCalled();
	expect(screen.queryByRole("button", { name: "Generate key" })).not.toBeInTheDocument();
});

test("creates the key and shows the full key in a dialog", async () => {
	const { hook, dialog } = await createKeyUntilDialog();

	expect(hook.addKey).toHaveBeenCalledWith({ name: "New key", scopes: ["read"] });
	expect(within(dialog).getByText(SECRET)).toBeInTheDocument();
	expect(within(dialog).getByText(/You won't be able to see it again/)).toBeInTheDocument();
	expect(within(dialog).getByText(/Expires on/)).toBeInTheDocument();
	// The form is closed after the creation.
	expect(screen.queryByLabelText("Key name")).not.toBeInTheDocument();
});

test("sends read and write when both are selected", async () => {
	const hook = mockHook({ addKey: vi.fn().mockResolvedValue(CREATED) });

	renderPage();
	clickPlus();
	fireEvent.click(screen.getByRole("button", { name: "Write" }));
	fillName("Both");
	fireEvent.click(screen.getByRole("button", { name: "Create" }));
	fireEvent.click(screen.getByRole("button", { name: "Generate key" }));

	await screen.findByRole("dialog");
	expect(hook.addKey).toHaveBeenCalledWith({ name: "Both", scopes: ["read", "write"] });
});

test("trims the name before sending it", async () => {
	const hook = mockHook({ addKey: vi.fn().mockResolvedValue(CREATED) });

	renderPage();
	submitForm("   My script   ");
	fireEvent.click(screen.getByRole("button", { name: "Generate key" }));

	await screen.findByRole("dialog");
	expect(hook.addKey).toHaveBeenCalledWith({ name: "My script", scopes: ["read"] });
});

test("does not close the key dialog when clicking outside of it", async () => {
	const { dialog } = await createKeyUntilDialog();

	// The dialog element is the full-screen overlay.
	fireEvent.click(dialog);

	expect(screen.getByRole("dialog")).toBeInTheDocument();
	expect(screen.getByText(SECRET)).toBeInTheDocument();
});

test("copies the key and closes the dialog", async () => {
	const writeText = vi.fn().mockResolvedValue(undefined);
	mockClipboard(writeText);
	await createKeyUntilDialog();

	fireEvent.click(screen.getByRole("button", { name: "Copy and close" }));

	await waitFor(() => expect(screen.queryByRole("dialog")).not.toBeInTheDocument());
	expect(writeText).toHaveBeenCalledWith(SECRET);
	expect(screen.queryByText(SECRET)).not.toBeInTheDocument();
});

test("keeps the dialog open when the copy fails, then lets the user close it", async () => {
	mockClipboard(vi.fn().mockRejectedValue(new Error("denied")));
	await createKeyUntilDialog();

	fireEvent.click(screen.getByRole("button", { name: "Copy and close" }));

	expect(await screen.findByRole("alert")).toHaveTextContent("Copy failed");
	expect(screen.getByText(SECRET)).toBeInTheDocument();

	fireEvent.click(screen.getByRole("button", { name: "Close anyway" }));

	await waitFor(() => expect(screen.queryByRole("dialog")).not.toBeInTheDocument());
});

test("does not show Close anyway before a copy has failed", async () => {
	await createKeyUntilDialog();

	expect(screen.queryByRole("button", { name: "Close anyway" })).not.toBeInTheDocument();
});

test("shows a message and reloads the list when the limit is reached (409)", async () => {
	const addKey = vi
		.fn()
		.mockRejectedValue(new ApiError(409, "API_KEY_LIMIT_REACHED", "limit reached"));
	const hook = mockHook({ addKey });

	renderPage();
	submitForm("New key");
	fireEvent.click(screen.getByRole("button", { name: "Generate key" }));

	expect(await screen.findByRole("alert")).toHaveTextContent("5 active keys");
	expect(hook.reload).toHaveBeenCalledTimes(1);
	expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
});

test("shows a message when the gateway is unavailable (503)", async () => {
	const addKey = vi.fn().mockRejectedValue(new ApiError(503, "HTTP_503", "unavailable"));
	const hook = mockHook({ addKey });

	renderPage();
	submitForm("New key");
	fireEvent.click(screen.getByRole("button", { name: "Generate key" }));

	expect(await screen.findByRole("alert")).toHaveTextContent("Service temporarily unavailable");
	expect(hook.reload).not.toHaveBeenCalled();
});

test("shows a message when the server cannot be reached", async () => {
	const addKey = vi.fn().mockRejectedValue(new Error("network"));
	mockHook({ addKey });

	renderPage();
	submitForm("New key");
	fireEvent.click(screen.getByRole("button", { name: "Generate key" }));

	expect(await screen.findByRole("alert")).toHaveTextContent("Unable to reach the server");
});

// ---------------------------------------------------------------------------
// Deletion
// ---------------------------------------------------------------------------

test("asks for a confirmation before deleting a key", () => {
	const hook = mockHook({ keys: [FIRST, SECOND] });

	renderPage();
	fireEvent.click(screen.getAllByRole("button", { name: "Delete" })[0]);

	expect(screen.getByText(/Delete "My script"/)).toBeInTheDocument();
	expect(hook.deleteKey).not.toHaveBeenCalled();
});

test("deletes the key once confirmed", async () => {
	const hook = mockHook({ keys: [FIRST, SECOND], deleteKey: vi.fn().mockResolvedValue(undefined) });

	renderPage();
	fireEvent.click(screen.getAllByRole("button", { name: "Delete" })[0]);
	// The confirmation dialog is rendered last, so its Delete button is the last one.
	fireEvent.click(screen.getAllByRole("button", { name: "Delete" }).at(-1)!);

	await waitFor(() => expect(hook.deleteKey).toHaveBeenCalledWith(FIRST.id));
	await waitFor(() => expect(screen.queryByText(/Delete "My script"/)).not.toBeInTheDocument());
});

test("does not delete the key when the confirmation is cancelled", () => {
	const hook = mockHook({ keys: [FIRST] });

	renderPage();
	fireEvent.click(screen.getByRole("button", { name: "Delete" }));
	fireEvent.click(screen.getByRole("button", { name: "Cancel" }));

	expect(hook.deleteKey).not.toHaveBeenCalled();
	expect(screen.queryByText(/Delete "My script"/)).not.toBeInTheDocument();
});

test("shows an error when the deletion fails", async () => {
	mockHook({ keys: [FIRST], deleteKey: vi.fn().mockRejectedValue(new Error("boom")) });

	renderPage();
	fireEvent.click(screen.getByRole("button", { name: "Delete" }));
	fireEvent.click(screen.getAllByRole("button", { name: "Delete" }).at(-1)!);

	expect(await screen.findByRole("alert")).toHaveTextContent("Unable to reach the server");
	expect(screen.getByText(FIRST.name)).toBeInTheDocument();
});

// ---------------------------------------------------------------------------
// Access
// ---------------------------------------------------------------------------

test("does not show the page to a logged out user", () => {
	mockHook();
	const loggedOut: AuthContextValue = {
		account: null,
		isLoggedIn: false,
		isLoading: false,
		signup: vi.fn(),
		login: vi.fn(),
		logout: vi.fn(),
	};

	render(
		<MemoryRouter initialEntries={["/dashboard/publicapikey"]}>
			<AuthContext value={loggedOut}>
				<ProfileProvider>
					<AppRouter />
				</ProfileProvider>
			</AuthContext>
		</MemoryRouter>,
	);

	expect(screen.queryByText("Manage your public API keys")).not.toBeInTheDocument();
	expect(useApiKeys).not.toHaveBeenCalled();
});
