import { apiFetch } from "@/shared/components/api/client";
import type { Profile, ProfileUpdate, TopicsResponse } from "@/features/profile/types";

export function getProfile(): Promise<Profile> {
	return apiFetch<Profile>(`/api/personalization/me/profile`);
}

export function updateProfile(update: ProfileUpdate): Promise<Profile> {
	return apiFetch<Profile>(`/api/personalization/me/profile`, {
		method: "PUT",
		body: update,
	});
}

export function getTopics(): Promise<TopicsResponse> {
	return apiFetch<TopicsResponse>(`/api/personalization/topics`);
}
