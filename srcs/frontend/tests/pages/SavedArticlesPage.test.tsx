import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, expect, test, vi } from "vitest";
import { AuthContext, type AuthContextValue } from "@/app/AuthContextDefinition";
import { NotificationProvider } from "@/app/NotificationContext";
import { AppRouter } from "@/app/router";
import { deleteSavedArticle, getSavedArticles } from "@/features/saved-articles/api";
import type { SavedArticle } from "@/features/saved-articles/types";
import { SavedArticles } from "@/pages/SavedArticlesPage";

// Each test decides what the API answers.
vi.mock("@/features/saved-articles/api", () => ({
	getSavedArticles: vi.fn(),
	deleteSavedArticle: vi.fn(),
}));

afterEach(() => {
	vi.mocked(getSavedArticles).mockReset();
	vi.mocked(deleteSavedArticle).mockReset();
});

// Shown first: the page sorts by reading time, shortest first.
const FIRST: SavedArticle = {
	article_id: "6f1c1b2e-1d2a-4c3b-9a8e-111111111111",
	title: "Open-source models narrow the enterprise gap",
	url: "https://www.aitechdaily.com/",
	summary: "Smaller teams gain access to capable models.",
	publisher_name: "TechDaily",
	topic_id: "technologies",
	read_time_minutes: 3,
	saved_at: "2026-11-03T08:00:00Z",
};

const SECOND: SavedArticle = {
	article_id: "6f1c1b2e-1d2a-4c3b-9a8e-222222222222",
	title: "Data centres race to secure clean power",
	url: "https://newenergyweekly.co.uk/",
	summary: "Operators are signing long-term energy contracts.",
	publisher_name: "Energy Weekly",
	topic_id: "technologies",
	read_time_minutes: 5,
	saved_at: "2026-11-02T08:00:00Z",
};

function answerWith(items: SavedArticle[]) {
	vi.mocked(getSavedArticles).mockResolvedValue({ items });
}

function renderPage() {
	render(
		<MemoryRouter>
			<NotificationProvider>
				<SavedArticles />
			</NotificationProvider>
		</MemoryRouter>,
	);
}

test("shows a spinner while the articles are loading", () => {
	// A promise that never resolves: the page stays in its loading state.
	vi.mocked(getSavedArticles).mockReturnValue(new Promise(() => undefined));

	renderPage();

	expect(screen.getByRole("status", { name: "Loading" })).toBeInTheDocument();
});

test("shows the empty state when no article is saved", async () => {
	answerWith([]);

	renderPage();

	expect(await screen.findByText("You haven't saved any article yet.")).toBeInTheDocument();
});

test("shows the saved articles from the API", async () => {
	answerWith([FIRST, SECOND]);

	renderPage();

	expect(await screen.findByText(FIRST.title)).toBeInTheDocument();
	expect(screen.getByText(SECOND.title)).toBeInTheDocument();
});

test("shows an error message when the articles cannot be loaded", async () => {
	vi.mocked(getSavedArticles).mockRejectedValue(new Error("boom"));

	renderPage();

	const message = await screen.findByText(
		"Your saved articles couldn't be loaded. Please try again later.",
	);
	expect(message).toBeInTheDocument();
});

test("removes the article when clicking Saved", async () => {
	answerWith([FIRST, SECOND]);
	vi.mocked(deleteSavedArticle).mockResolvedValue(undefined);

	renderPage();
	fireEvent.click((await screen.findAllByRole("button", { name: "Saved" }))[0]);

	expect(deleteSavedArticle).toHaveBeenCalledWith(FIRST.article_id);
	await waitFor(() => expect(screen.queryByText(FIRST.title)).not.toBeInTheDocument());
	expect(screen.getByText(SECOND.title)).toBeInTheDocument();
	expect(screen.getByRole("status")).toHaveTextContent(
		"The article has been removed from your saved articles.",
	);
});

test("keeps the article when the removal fails", async () => {
	answerWith([FIRST, SECOND]);
	vi.mocked(deleteSavedArticle).mockRejectedValue(new Error("boom"));

	renderPage();
	fireEvent.click((await screen.findAllByRole("button", { name: "Saved" }))[0]);

	// Wait for the error, otherwise the checks below would run before the answer.
	expect(await screen.findByRole("alert")).toHaveTextContent(
		"The article could not be removed, please try again.",
	);
	expect(screen.getByText(FIRST.title)).toBeInTheDocument();
	expect(screen.getByText(SECOND.title)).toBeInTheDocument();
});

test("shows the link to the original article", async () => {
	answerWith([FIRST]);

	renderPage();
	fireEvent.click(await screen.findByRole("button", { name: "Read More →" }));

	expect(screen.getByText("Read the full article on TechDaily ↗")).toBeInTheDocument();
});

test("filters saved articles by publisher", async () => {
	answerWith([FIRST, SECOND]);

	renderPage();
	await screen.findByText(FIRST.title);
	fireEvent.change(screen.getByLabelText("Source"), { target: { value: "Energy Weekly" } });

	expect(screen.queryByText(FIRST.title)).not.toBeInTheDocument();
	expect(screen.getByText(SECOND.title)).toBeInTheDocument();
});

test("shows the filtered state when no article matches the filters", async () => {
	answerWith([FIRST, SECOND]);

	renderPage();
	fireEvent.change(await screen.findByLabelText("Search"), { target: { value: "nonexistent" } });

	expect(screen.getByText("No article matches the filters.")).toBeInTheDocument();
	expect(screen.queryByText(FIRST.title)).not.toBeInTheDocument();
});

test("opens the right article when clicking Read more", async () => {
	answerWith([FIRST, SECOND]);

	renderPage();
	fireEvent.click((await screen.findAllByRole("button", { name: "Read More →" }))[1]);

	// The title is also on the card, so look for it inside the modal only.
	const dialog = screen.getByRole("dialog");
	expect(within(dialog).getByText(SECOND.title)).toBeInTheDocument();
});

test("does not show the page to a logged out user", () => {
	const loggedOut: AuthContextValue = {
		account: null,
		isLoggedIn: false,
		isLoading: false,
		profileComplete: false,
		signup: vi.fn(),
		completeProfile: vi.fn(),
		login: vi.fn(),
		logout: vi.fn(),
	};

	render(
		<MemoryRouter initialEntries={["/dashboard/saved"]}>
			<AuthContext value={loggedOut}>
				<AppRouter />
			</AuthContext>
		</MemoryRouter>,
	);

	expect(screen.queryByText("Saved Articles")).not.toBeInTheDocument();
	expect(getSavedArticles).not.toHaveBeenCalled();
});
