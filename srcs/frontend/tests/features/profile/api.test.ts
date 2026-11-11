import { afterEach, describe, expect, test, vi } from "vitest";
import { getProfile, type Profile } from "@/features/profile/api";
import { apiFetch } from "@/shared/components/api/client";

vi.mock("@/shared/components/api/client", async (importOriginal) => ({
	...(await importOriginal<typeof import("@/shared/components/api/client")>()),
	apiFetch: vi.fn(),
}));

const PROFILE: Profile = {
	name: "Kate",
	topic_ids: ["science"],
	created_at: "2026-11-01T08:00:00Z",
	updated_at: "2026-11-01T08:00:00Z",
};

afterEach(() => {
	vi.mocked(apiFetch).mockReset();
});

describe("getProfile", () => {
	test("returns the profile", async () => {
		vi.mocked(apiFetch).mockResolvedValue(PROFILE);

		await expect(getProfile()).resolves.toEqual(PROFILE);
		expect(apiFetch).toHaveBeenCalledWith("/api/personalization/me/profile");
	});

	test("returns null when there is no profile yet (200 with null, not a 404)", async () => {
		vi.mocked(apiFetch).mockResolvedValue(null);

		await expect(getProfile()).resolves.toBeNull();
	});
});
