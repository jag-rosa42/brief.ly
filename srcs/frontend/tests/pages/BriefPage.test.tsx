import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { afterEach, expect, test, vi } from "vitest";
import { getBriefing } from "@/features/briefing/api";
import type { Briefing, BriefingArticle } from "@/features/briefing/types";
import { ApiError } from "@/shared/components/api/client";
import { BriefPage } from "@/pages/BriefPage";

// Each test decides what the API answers.
vi.mock("@/features/briefing/api", () => ({
	getBriefing: vi.fn(),
}));

afterEach(() => {
	vi.mocked(getBriefing).mockReset();
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
	summary: null,
	read_time_minutes: 0,
	topic_id: "health",
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
			<Routes>
				<Route path="/dashboard/brief" element={<BriefPage />} />
				<Route path="/dashboard/profile" element={<p>Profile form</p>} />
			</Routes>
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

	expect(await screen.findByText("Good morning Kate!")).toBeInTheDocument();
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
