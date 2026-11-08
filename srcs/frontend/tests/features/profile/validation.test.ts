import { describe, expect, test } from "vitest";
import { buildPayload, type Profile } from "@/features/profile/api";
import { mapProfileError, validate } from "@/features/profile/validation";
import { ApiError } from "@/shared/components/api/client";

const PROFILE: Profile = {
	name: "Kate",
	topic_ids: ["science", "health"],
	created_at: "2026-11-01T08:00:00Z",
	updated_at: "2026-11-01T08:00:00Z",
};

describe("buildPayload", () => {
	test("sends both fields, trimmed, when the profile is created", () => {
		expect(buildPayload(null, { name: " Kate ", topicIds: ["science"] })).toEqual({
			name: "Kate",
			topic_ids: ["science"],
		});
	});

	test("only sends the fields that changed", () => {
		expect(buildPayload(PROFILE, { name: "Katherine", topicIds: ["science", "health"] })).toEqual({
			name: "Katherine",
		});
		expect(buildPayload(PROFILE, { name: "Kate", topicIds: ["science"] })).toEqual({
			topic_ids: ["science"],
		});
	});

	test("sends nothing when only the order of the interests changed", () => {
		expect(buildPayload(PROFILE, { name: " Kate ", topicIds: ["health", "science"] })).toEqual({});
	});
});

describe("validate", () => {
	test("accepts a name of 1 to 50 characters and 1 to 4 interests", () => {
		expect(validate("K", ["science"])).toEqual({});
		expect(validate("K".repeat(50), ["a", "b", "c", "d"])).toEqual({});
	});

	test("refuses an empty name, once trimmed", () => {
		expect(validate("   ", ["science"]).name).toBe("Name must be at least 1 characters.");
	});

	test("refuses a name longer than 50 characters", () => {
		expect(validate("K".repeat(51), ["science"]).name).toBe("Name must be at most 50 characters.");
	});

	test("refuses no interest or more than four", () => {
		expect(validate("Kate", []).topics).toBe("Pick between 1 and 4 interests.");
		expect(validate("Kate", ["a", "b", "c", "d", "e"]).topics).toBe(
			"Pick between 1 and 4 interests.",
		);
	});
});

describe("mapProfileError", () => {
	test("puts each validation detail under its field", () => {
		const error = new ApiError(422, "VALIDATION_ERROR", "Some fields are invalid", [
			{ field: "name", message: "Name is too long" },
			{ field: "topic_ids", message: "Unknown topic: a" },
			{ field: "topic_ids", message: "Unknown topic: b" },
		]);

		expect(mapProfileError(error)).toEqual({
			name: "Name is too long",
			topics: "Unknown topic: a Unknown topic: b",
		});
	});

	test("shows a general message for a validation error without details", () => {
		expect(mapProfileError(new ApiError(422, "VALIDATION_ERROR", "Invalid"))).toEqual({
			form: "Some information is invalid. Please check your entries and try again.",
		});
	});

	test.each([502, 503, 504])("says the service is unavailable on a %i", (status) => {
		expect(mapProfileError(new ApiError(status, "SERVICE_UNAVAILABLE", "Unavailable"))).toEqual({
			form: "Service temporarily unavailable. Please try again later.",
		});
	});

	test("never shows the raw message of a network error", () => {
		expect(mapProfileError(new TypeError("Failed to fetch"))).toEqual({
			form: "Unable to reach the server. Check your connection and try again.",
		});
	});

	test("shows a general message for any other error", () => {
		expect(mapProfileError(new ApiError(500, "INTERNAL_ERROR", "Boom"))).toEqual({
			form: "Unable to save your profile. Please try again.",
		});
	});
});
