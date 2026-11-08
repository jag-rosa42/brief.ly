import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { afterEach, expect, test, vi } from "vitest";
import { ProfileContext, type ProfileContextValue } from "@/app/ProfileContextDefinition";
import { getTopics, upsertProfile, type Profile } from "@/features/profile/api";
import { ApiError } from "@/shared/components/api/client";
import { ProfilePage } from "@/pages/ProfilePage";
import { NotificationProvider } from "@/app/NotificationContext";

// Each test decides what the API answers. buildPayload stays the real one:
// it is what decides which fields the PUT sends.
vi.mock("@/features/profile/api", async (importOriginal) => ({
	...(await importOriginal<typeof import("@/features/profile/api")>()),
	getTopics: vi.fn(),
	upsertProfile: vi.fn(),
}));

afterEach(() => {
	vi.mocked(getTopics).mockReset();
	vi.mocked(upsertProfile).mockReset();
});

const PROFILE: Profile = {
	name: "Kate",
	topic_ids: ["science"],
	created_at: "2026-11-01T08:00:00Z",
	updated_at: "2026-11-01T08:00:00Z",
};

const TOPICS = [
	{ id: "business" },
	{ id: "health" },
	{ id: "science" },
	{ id: "sports" },
	{ id: "technology" },
];

// The label also holds the error message of the field, when there is one.
const NAME_FIELD = /^Name/;

// The dashboard only shows the page once the profile is loaded, so the tests
// give the page a loaded profile (or null: no profile yet, onboarding).
function renderPage(profile: Profile | null) {
	const context: ProfileContextValue = {
		profile,
		isProfileComplete: profile !== null,
		setProfile: vi.fn(),
		loading: false,
		error: null,
		reload: vi.fn(),
	};

	render(
		<MemoryRouter initialEntries={["/dashboard/profile"]}>
			<NotificationProvider>
				<ProfileContext value={context}>
					<Routes>
						<Route path="/dashboard/profile" element={<ProfilePage />} />
						<Route path="/dashboard/brief" element={<p>Brief page</p>} />
						<Route path="/" element={<p>Landing page</p>} />
					</Routes>
				</ProfileContext>
			</NotificationProvider>
		</MemoryRouter>,
	);

	return context;
}

test("shows the topics from the API", async () => {
	vi.mocked(getTopics).mockResolvedValue(TOPICS);

	renderPage(null);

	expect(await screen.findByRole("button", { name: "Technology" })).toBeInTheDocument();
	expect(screen.getByRole("button", { name: "Sports" })).toBeInTheDocument();
});

test("fills the form with the existing profile", async () => {
	vi.mocked(getTopics).mockResolvedValue(TOPICS);

	renderPage(PROFILE);

	expect(await screen.findByRole("button", { name: "Science" })).toHaveAttribute(
		"aria-pressed",
		"true",
	);
	expect(screen.getByLabelText(NAME_FIELD)).toHaveValue("Kate");
	expect(screen.getByRole("button", { name: "Business" })).toHaveAttribute("aria-pressed", "false");
});

test("creates the profile with both fields, then opens the brief", async () => {
	vi.mocked(getTopics).mockResolvedValue(TOPICS);
	const saved = { ...PROFILE, topic_ids: ["business"] };
	vi.mocked(upsertProfile).mockResolvedValue(saved);

	const context = renderPage(null);
	fireEvent.click(await screen.findByRole("button", { name: "Business" }));
	fireEvent.change(screen.getByLabelText(NAME_FIELD), { target: { value: " Kate " } });
	fireEvent.click(screen.getByRole("button", { name: "Save" }));

	expect(await screen.findByText("Brief page")).toBeInTheDocument();
	expect(upsertProfile).toHaveBeenCalledWith({ name: "Kate", topic_ids: ["business"] });
	// The shared profile is updated: the header and the dashboard see it at once.
	expect(context.setProfile).toHaveBeenCalledWith(saved);
	expect(screen.getByText("Your profile has been created.")).toBeInTheDocument();
});

test("only sends the fields that changed", async () => {
	vi.mocked(getTopics).mockResolvedValue(TOPICS);
	vi.mocked(upsertProfile).mockResolvedValue({ ...PROFILE, name: "Katherine" });

	renderPage(PROFILE);
	fireEvent.change(await screen.findByLabelText(NAME_FIELD), {
		target: { value: "Katherine" },
	});
	fireEvent.click(screen.getByRole("button", { name: "Save" }));

	expect(await screen.findByText("Your profile has been updated.")).toBeInTheDocument();
	expect(upsertProfile).toHaveBeenCalledWith({ name: "Katherine" });
	// An update stays on the page.
	expect(screen.queryByText("Brief page")).not.toBeInTheDocument();
});

test("disables Save while nothing changed", async () => {
	vi.mocked(getTopics).mockResolvedValue(TOPICS);

	renderPage(PROFILE);

	await screen.findByRole("button", { name: "Science" });
	expect(screen.getByRole("button", { name: "Save" })).toBeDisabled();
});

test("checks the fields before calling the API", async () => {
	vi.mocked(getTopics).mockResolvedValue(TOPICS);

	renderPage(null);
	await screen.findByRole("button", { name: "Business" });
	fireEvent.click(screen.getByRole("button", { name: "Save" }));

	expect(await screen.findByText("Name must be at least 1 characters.")).toBeInTheDocument();
	expect(screen.getByText("Pick between 1 and 4 interests.")).toBeInTheDocument();
	expect(upsertProfile).not.toHaveBeenCalled();
});

test("accepts a name longer than 14 characters", async () => {
	vi.mocked(getTopics).mockResolvedValue(TOPICS);
	vi.mocked(upsertProfile).mockResolvedValue({ ...PROFILE, name: "Katherine Elizabeth Johnson" });

	renderPage(PROFILE);
	fireEvent.change(await screen.findByLabelText(NAME_FIELD), {
		target: { value: "Katherine Elizabeth Johnson" },
	});
	fireEvent.click(screen.getByRole("button", { name: "Save" }));

	expect(await screen.findByText("Your profile has been updated.")).toBeInTheDocument();
});

test("lets the user pick four interests at most", async () => {
	vi.mocked(getTopics).mockResolvedValue(TOPICS);

	renderPage(null);
	for (const name of ["Business", "Health", "Science", "Sports"]) {
		fireEvent.click(await screen.findByRole("button", { name }));
	}

	expect(screen.getByRole("button", { name: "Technology" })).toBeDisabled();
	// A picked interest can still be removed.
	expect(screen.getByRole("button", { name: "Sports" })).toBeEnabled();
});

test("shows a validation error from the API under its field", async () => {
	vi.mocked(getTopics).mockResolvedValue(TOPICS);
	vi.mocked(upsertProfile).mockRejectedValue(
		new ApiError(422, "VALIDATION_ERROR", "Some fields are invalid", [
			{ field: "topic_ids", message: "Unknown topic: business" },
		]),
	);

	renderPage(PROFILE);
	fireEvent.click(await screen.findByRole("button", { name: "Business" }));
	fireEvent.click(screen.getByRole("button", { name: "Save" }));

	expect(await screen.findByText("Unknown topic: business")).toBeInTheDocument();
	expect(screen.getByLabelText(NAME_FIELD)).toHaveValue("Kate");
	// The field error is the only alert: no error notification on top of it.
	expect(screen.getAllByRole("alert")).toHaveLength(1);
});

test("keeps the values and shows a clear message when the server cannot be reached", async () => {
	vi.mocked(getTopics).mockResolvedValue(TOPICS);
	// What fetch throws when the network is down: not an ApiError.
	vi.mocked(upsertProfile).mockRejectedValue(new TypeError("Failed to fetch"));

	renderPage(PROFILE);
	fireEvent.change(await screen.findByLabelText(NAME_FIELD), {
		target: { value: "Katherine" },
	});
	fireEvent.click(screen.getByRole("button", { name: "Save" }));

	expect(
		await screen.findByText("Unable to reach the server. Check your connection and try again."),
	).toBeInTheDocument();
	expect(screen.queryByText("Failed to fetch")).not.toBeInTheDocument();
	expect(screen.getByLabelText(NAME_FIELD)).toHaveValue("Katherine");
});

test("shows a retry button when the topics cannot be loaded", async () => {
	vi.mocked(getTopics)
		.mockRejectedValueOnce(new ApiError(503, "SERVICE_UNAVAILABLE", "Service unavailable"))
		.mockResolvedValueOnce(TOPICS);

	renderPage(PROFILE);

	expect(await screen.findByRole("alert")).toHaveTextContent("Unable to load interests.");
	// The rest of the page stays: only the interests are replaced.
	expect(screen.getByText("Profile")).toBeInTheDocument();
	expect(screen.getByLabelText(NAME_FIELD)).toHaveValue("Kate");

	fireEvent.click(screen.getByRole("button", { name: "Retry" }));

	expect(await screen.findByRole("button", { name: "Science" })).toBeInTheDocument();
	expect(screen.queryByRole("alert")).not.toBeInTheDocument();
});

test("goes back to the brief when the user has a profile", async () => {
	vi.mocked(getTopics).mockResolvedValue(TOPICS);

	renderPage(PROFILE);
	fireEvent.click(await screen.findByRole("link", { name: "Back" }));

	expect(screen.getByText("Brief page")).toBeInTheDocument();
});

test("goes back to the landing page during the onboarding", async () => {
	vi.mocked(getTopics).mockResolvedValue(TOPICS);

	renderPage(null);
	fireEvent.click(await screen.findByRole("link", { name: "Back" }));

	expect(screen.getByText("Landing page")).toBeInTheDocument();
});
