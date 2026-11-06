import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { afterEach, expect, test, vi } from "vitest";
import { AuthContext, type AuthContextValue } from "@/app/AuthContextDefinition";
import { PreferencesProvider } from "@/app/PreferencesContext";
import { getProfile, getTopics, updateProfile } from "@/features/profile/api";
import type { Profile } from "@/features/profile/types";
import { ApiError } from "@/shared/components/api/client";
import { ProfilePage } from "@/pages/ProfilePage";

// Each test decides what the API answers.
vi.mock("@/features/profile/api", () => ({
	getProfile: vi.fn(),
	getTopics: vi.fn(),
	updateProfile: vi.fn(),
}));

afterEach(() => {
	vi.mocked(getProfile).mockReset();
	vi.mocked(getTopics).mockReset();
	vi.mocked(updateProfile).mockReset();
});

const PROFILE: Profile = {
	name: "Kate",
	topic_ids: ["science"],
	created_at: "2026-11-01T08:00:00Z",
	updated_at: "2026-11-01T08:00:00Z",
};

function answerWith(profile: Profile | null) {
	vi.mocked(getTopics).mockResolvedValue({
		items: [{ id: "business" }, { id: "science" }, { id: "sports" }, { id: "technology" }],
	});
	if (profile === null) {
		vi.mocked(getProfile).mockRejectedValue(
			new ApiError(404, "PROFILE_NOT_FOUND", "Profile not found"),
		);
	} else {
		vi.mocked(getProfile).mockResolvedValue(profile);
	}
}

function renderPage(profileComplete: boolean) {
	const auth: AuthContextValue = {
		account: null,
		isLoggedIn: true,
		isLoading: false,
		profileComplete,
		signup: vi.fn(),
		completeProfile: vi.fn(),
		login: vi.fn(),
		logout: vi.fn(),
	};

	render(
		<MemoryRouter initialEntries={["/dashboard/profile"]}>
			<AuthContext value={auth}>
				<PreferencesProvider>
					<Routes>
						<Route path="/dashboard/profile" element={<ProfilePage />} />
						<Route path="/dashboard/brief" element={<p>Brief page</p>} />
					</Routes>
				</PreferencesProvider>
			</AuthContext>
		</MemoryRouter>,
	);

	return auth;
}

test("shows the topics from the API", async () => {
	answerWith(null);

	renderPage(false);

	expect(await screen.findByRole("button", { name: "Technology" })).toBeInTheDocument();
	expect(screen.getByRole("button", { name: "Sports" })).toBeInTheDocument();
});

test("fills the form with the existing profile", async () => {
	answerWith(PROFILE);

	renderPage(true);

	expect(await screen.findByLabelText("Name")).toHaveValue("Kate");
	expect(screen.getByRole("button", { name: "Science" })).toHaveAttribute("aria-pressed", "true");
});

test("marks the onboarding as done when the user already has a profile", async () => {
	answerWith(PROFILE);

	const auth = renderPage(false);

	await waitFor(() => expect(auth.completeProfile).toHaveBeenCalled());
});

test("creates the profile with both fields, then opens the brief", async () => {
	answerWith(null);
	vi.mocked(updateProfile).mockResolvedValue({ ...PROFILE, topic_ids: ["business"] });

	const auth = renderPage(false);
	fireEvent.change(await screen.findByLabelText("Name"), { target: { value: " Kate " } });
	fireEvent.click(screen.getByRole("button", { name: "Business" }));
	fireEvent.click(screen.getByRole("button", { name: "Save" }));

	expect(await screen.findByText("Brief page")).toBeInTheDocument();
	expect(updateProfile).toHaveBeenCalledWith({ name: "Kate", topic_ids: ["business"] });
	expect(auth.completeProfile).toHaveBeenCalled();
});

test("only sends the fields that changed", async () => {
	answerWith(PROFILE);
	vi.mocked(updateProfile).mockResolvedValue({ ...PROFILE, name: "Katherine" });

	renderPage(true);
	fireEvent.change(await screen.findByLabelText("Name"), { target: { value: "Katherine" } });
	fireEvent.click(screen.getByRole("button", { name: "Save" }));

	expect(await screen.findByText("Profile saved")).toBeInTheDocument();
	expect(updateProfile).toHaveBeenCalledWith({ name: "Katherine" });
});

test("does not call the API when nothing changed", async () => {
	answerWith(PROFILE);

	renderPage(true);
	fireEvent.click(await screen.findByRole("button", { name: "Save" }));

	expect(await screen.findByText("Profile saved")).toBeInTheDocument();
	expect(updateProfile).not.toHaveBeenCalled();
});

test("shows a validation error from the API under its field", async () => {
	answerWith(PROFILE);
	vi.mocked(updateProfile).mockRejectedValue(
		new ApiError(422, "VALIDATION_ERROR", "Some fields are invalid", [
			{ field: "topic_ids", message: "Unknown topic: science" },
		]),
	);

	renderPage(true);
	fireEvent.click(await screen.findByRole("button", { name: "Business" }));
	fireEvent.click(screen.getByRole("button", { name: "Save" }));

	expect(await screen.findByText("Unknown topic: science")).toBeInTheDocument();
	expect(screen.getByLabelText("Name")).toHaveValue("Kate");
});

test("keeps the values and shows an error when the save fails", async () => {
	answerWith(PROFILE);
	vi.mocked(updateProfile).mockRejectedValue(new Error("Network down"));

	renderPage(true);
	fireEvent.change(await screen.findByLabelText("Name"), { target: { value: "Katherine" } });
	fireEvent.click(screen.getByRole("button", { name: "Save" }));

	expect(
		await screen.findByText("The profile could not be saved, please try again."),
	).toBeInTheDocument();
	expect(screen.getByLabelText("Name")).toHaveValue("Katherine");
});

test("shows an error when the topics cannot be loaded", async () => {
	answerWith(PROFILE);
	vi.mocked(getTopics).mockRejectedValue(
		new ApiError(503, "SERVICE_UNAVAILABLE", "Service unavailable"),
	);

	renderPage(true);

	expect(await screen.findByRole("alert")).toHaveTextContent("Failed to load your profile.");
});
