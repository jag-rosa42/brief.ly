import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { afterEach, expect, test, vi } from "vitest";
import { getBriefing } from "@/features/briefing/api";
import type { Briefing, BriefingArticle } from "@/features/briefing/types";
import { deleteSavedArticle, saveArticle } from "@/features/saved-articles/api";
import { MAX_SAVED_ARTICLES } from "@/features/saved-articles/constants";
import { ApiError } from "@/shared/components/api/client";
import { NotificationProvider } from "@/app/NotificationContext";
import { BriefPage } from "@/pages/BriefPage";

// Each test decides what the API answers.
vi.mock("@/features/briefing/api", () => ({
	getBriefing: vi.fn(),
}));
vi.mock("@/features/saved-articles/api", () => ({
	saveArticle: vi.fn(),
	deleteSavedArticle: vi.fn(),
}));

afterEach(() => {
	vi.mocked(getBriefing).mockReset();
	vi.mocked(saveArticle).mockReset();
	vi.mocked(deleteSavedArticle).mockReset();
});

const FIRST: BriefingArticle = {
	article_id: "6f1c1b2e-1d2a-4c3b-9a8e-111111111111",
	title: "Open-source models narrow the enterprise gap",
	publisher_name: "TechDaily",
	url: "https://www.aitechdaily.com/",
	summary: "Smaller teams gain access to capable models.",
	read_time_minutes: 3,
	topic_id: "technologies",
};

const SECOND: BriefingArticle = {
	article_id: "6f1c1b2e-1d2a-4c3b-9a8e-222222222222",
	title: "Researchers examine the link between sleep and health",
	publisher_name: "Health Monitor",
	url: "https://example.com/sleep",
	summary: "Regular sleep is linked to better long-term health.",
	read_time_minutes: 0,
	topic_id: "health",
};

const WITHOUT_SUMMARY: BriefingArticle = {
	article_id: "6f1c1b2e-1d2a-4c3b-9a8e-333333333333",
	title: "A story whose summary is not ready yet",
	publisher_name: "TechDaily",
	url: "https://example.com/no-summary",
	summary: null,
	read_time_minutes: 2,
	topic_id: "technologies",
};

function briefing(overrides: Partial<Briefing> = {}): Briefing {
	return {
		profile: {
			name: "Kate",
			topic_ids: ["technologies", "health"],
			saved_article_ids: [],
		},
		topic_clusters: [
			{
				topic_id: "technologies",
				summary: "Open-source models keep narrowing the gap.",
				articles: [FIRST],
			},
			{ topic_id: "health", summary: null, articles: [SECOND] },
		],
		...overrides,
	};
}

function renderPage() {
	render(
		<MemoryRouter initialEntries={["/dashboard/brief"]}>
			<NotificationProvider>
				<Routes>
					<Route path="/dashboard/brief" element={<BriefPage />} />
					<Route path="/dashboard/profile" element={<p>Profile form</p>} />
				</Routes>
			</NotificationProvider>
		</MemoryRouter>,
	);
}

test("shows a spinner while the briefing is loading", () => {
	// A promise that never resolves: the page stays in its loading state.
	vi.mocked(getBriefing).mockReturnValue(new Promise(() => undefined));

	renderPage();

	expect(screen.getByRole("status", { name: "Loading" })).toBeInTheDocument();
});

test("greets the user by the name of their profile", async () => {
	vi.mocked(getBriefing).mockResolvedValue(briefing());

	renderPage();

	// The name is in its own span (to truncate a long one): read the whole heading.
	expect(await screen.findByRole("heading", { level: 1 })).toHaveTextContent("Good morning Kate!");
});

test("shows one tab per interest, in the profile's order", async () => {
	vi.mocked(getBriefing).mockResolvedValue(briefing());

	renderPage();

	const tabs = await screen.findAllByRole("tab");
	expect(tabs.map((tab) => tab.textContent)).toEqual(["Technologies", "Health"]);
});

test("shows the summary and the articles of the first topic", async () => {
	vi.mocked(getBriefing).mockResolvedValue(briefing());

	renderPage();

	expect(await screen.findByText("Open-source models keep narrowing the gap.")).toBeInTheDocument();
	expect(screen.getByText(FIRST.title)).toBeInTheDocument();
	expect(screen.getByText("TechDaily")).toBeInTheDocument();
	expect(screen.queryByText(SECOND.title)).not.toBeInTheDocument();
});

test("shows the articles of another topic when its tab is clicked", async () => {
	vi.mocked(getBriefing).mockResolvedValue(briefing());

	renderPage();
	fireEvent.click(await screen.findByRole("tab", { name: "Health" }));

	expect(screen.getByText(SECOND.title)).toBeInTheDocument();
	expect(screen.queryByText(FIRST.title)).not.toBeInTheDocument();
});

test("says when the summary of a topic is not ready", async () => {
	vi.mocked(getBriefing).mockResolvedValue(briefing());

	renderPage();
	fireEvent.click(await screen.findByRole("tab", { name: "Health" }));

	expect(screen.getByText("The summary of this topic is not ready yet.")).toBeInTheDocument();
});

test("says when a topic has no article today", async () => {
	vi.mocked(getBriefing).mockResolvedValue(
		briefing({ topic_clusters: [{ topic_id: "technologies", summary: null, articles: [] }] }),
	);

	renderPage();

	expect(await screen.findByText("No story for this topic today.")).toBeInTheDocument();
});

test("hides the articles that have no summary yet", async () => {
	vi.mocked(getBriefing).mockResolvedValue(
		briefing({
			topic_clusters: [
				{ topic_id: "technologies", summary: null, articles: [FIRST, WITHOUT_SUMMARY] },
			],
		}),
	);

	renderPage();

	expect(await screen.findByText(FIRST.title)).toBeInTheDocument();
	expect(screen.queryByText(WITHOUT_SUMMARY.title)).not.toBeInTheDocument();
});

test("says there is no story when no article has a summary yet", async () => {
	vi.mocked(getBriefing).mockResolvedValue(
		briefing({
			topic_clusters: [{ topic_id: "technologies", summary: null, articles: [WITHOUT_SUMMARY] }],
		}),
	);

	renderPage();

	expect(await screen.findByText("No story for this topic today.")).toBeInTheDocument();
	expect(screen.queryByText(WITHOUT_SUMMARY.title)).not.toBeInTheDocument();
});

test("marks the articles already saved", async () => {
	vi.mocked(getBriefing).mockResolvedValue(
		briefing({
			profile: {
				name: "Kate",
				topic_ids: ["technologies"],
				saved_article_ids: [FIRST.article_id],
			},
		}),
	);

	renderPage();

	expect(await screen.findByRole("button", { name: "Saved" })).toHaveAttribute(
		"aria-pressed",
		"true",
	);
});

test("saves an article", async () => {
	vi.mocked(getBriefing).mockResolvedValue(briefing());
	vi.mocked(saveArticle).mockResolvedValue({ ...FIRST, saved_at: "2026-11-07T08:00:00Z" });

	renderPage();
	fireEvent.click(await screen.findByRole("button", { name: "Save" }));

	expect(await screen.findByRole("button", { name: "Saved" })).toHaveAttribute(
		"aria-pressed",
		"true",
	);
	expect(saveArticle).toHaveBeenCalledWith(FIRST.article_id);
	expect(screen.getByRole("status")).toHaveTextContent(
		"The article has been added to your saved articles.",
	);
});

test("removes an article already saved", async () => {
	vi.mocked(getBriefing).mockResolvedValue(
		briefing({
			profile: {
				name: "Kate",
				topic_ids: ["technologies"],
				saved_article_ids: [FIRST.article_id],
			},
		}),
	);
	vi.mocked(deleteSavedArticle).mockResolvedValue(undefined);

	renderPage();
	fireEvent.click(await screen.findByRole("button", { name: "Saved" }));

	expect(await screen.findByRole("button", { name: "Save" })).toHaveAttribute(
		"aria-pressed",
		"false",
	);
	expect(deleteSavedArticle).toHaveBeenCalledWith(FIRST.article_id);
	// Already saved: clicking removes it, it is never saved twice.
	expect(saveArticle).not.toHaveBeenCalled();
	expect(screen.getByRole("status")).toHaveTextContent(
		"The article has been removed from your saved articles.",
	);
});

test("keeps the article saved when the removal fails", async () => {
	vi.mocked(getBriefing).mockResolvedValue(
		briefing({
			profile: {
				name: "Kate",
				topic_ids: ["technologies"],
				saved_article_ids: [FIRST.article_id],
			},
		}),
	);
	vi.mocked(deleteSavedArticle).mockRejectedValue(
		new ApiError(503, "SERVICE_UNAVAILABLE", "Service unavailable"),
	);

	renderPage();
	fireEvent.click(await screen.findByRole("button", { name: "Saved" }));

	expect(await screen.findByRole("alert")).toHaveTextContent(
		"The article could not be removed, please try again.",
	);
	expect(screen.getByRole("button", { name: "Saved" })).toHaveAttribute("aria-pressed", "true");
});

test.each([
	[
		"the article does not exist anymore",
		new ApiError(404, "ARTICLE_NOT_FOUND", "Article not found"),
	],
	["the user has no profile anymore", new ApiError(404, "PROFILE_NOT_FOUND", "Profile not found")],
])("keeps the article unsaved when %s", async (_case, error) => {
	vi.mocked(getBriefing).mockResolvedValue(briefing());
	vi.mocked(saveArticle).mockRejectedValue(error);

	renderPage();
	fireEvent.click(await screen.findByRole("button", { name: "Save" }));

	// Wait for the error, otherwise the checks below would run before the answer.
	expect(await screen.findByRole("alert")).toHaveTextContent(
		"The article could not be saved, please try again.",
	);
	// The page waits for the answer: on an error, nothing changes.
	expect(screen.getByRole("button", { name: "Save" })).toHaveAttribute("aria-pressed", "false");
	expect(screen.queryByRole("button", { name: "Saved" })).not.toBeInTheDocument();
});

test("says what to do when the saved articles limit is reached", async () => {
	vi.mocked(getBriefing).mockResolvedValue(briefing());
	vi.mocked(saveArticle).mockRejectedValue(
		new ApiError(409, "SAVED_ARTICLES_LIMIT_REACHED", "Saved articles limit reached"),
	);

	renderPage();
	fireEvent.click(await screen.findByRole("button", { name: "Save" }));

	// Trying again would fail the same way: the message says what to do instead.
	expect(await screen.findByRole("alert")).toHaveTextContent(
		`You can save up to ${MAX_SAVED_ARTICLES} articles: remove one from Saved first.`,
	);
	expect(screen.getByRole("button", { name: "Save" })).toHaveAttribute("aria-pressed", "false");
});

test("sends one request when the button is clicked twice quickly", async () => {
	vi.mocked(getBriefing).mockResolvedValue(briefing());
	// The first request is still running when the second click happens.
	let answer: () => void = () => undefined;
	vi.mocked(saveArticle).mockReturnValue(
		new Promise((resolve) => {
			answer = () => resolve({ ...FIRST, saved_at: "2026-11-07T08:00:00Z" });
		}),
	);

	renderPage();
	const button = await screen.findByRole("button", { name: "Save" });
	fireEvent.click(button);
	fireEvent.click(button);
	answer();

	expect(await screen.findByRole("button", { name: "Saved" })).toBeInTheDocument();
	expect(saveArticle).toHaveBeenCalledOnce();
});

test("sends the user to the profile form when they have no profile", async () => {
	vi.mocked(getBriefing).mockRejectedValue(
		new ApiError(404, "PROFILE_NOT_FOUND", "Profile not found"),
	);

	renderPage();

	expect(await screen.findByText("Profile form")).toBeInTheDocument();
});

test("shows an error when the briefing cannot be loaded", async () => {
	vi.mocked(getBriefing).mockRejectedValue(
		new ApiError(503, "SERVICE_UNAVAILABLE", "Service unavailable"),
	);

	renderPage();

	expect(await screen.findByRole("alert")).toHaveTextContent(
		"Something went wrong. Please try again.",
	);
});
