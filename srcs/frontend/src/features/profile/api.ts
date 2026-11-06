import { apiFetch, ApiError } from "@/shared/components/api/client";

export interface Profile {
	name: string;
	topic_ids: string[];
	created_at: string;
	updated_at: string;
}

export interface Topic {
	id: string;
}

export interface UpsertProfileBody {
	name?: string;
	topic_ids?: string[];
}

// 404 PROFILE_NOT_FOUND n'est pas une erreur : c'est le mode onboarding.
export async function getProfile(): Promise<Profile | null> {
	try {
		return await apiFetch<Profile>("/api/personalization/me/profile");
	} catch (e) {
		if (e instanceof ApiError && e.code === "PROFILE_NOT_FOUND") return null;
		throw e;
	}
}

export async function getTopics(): Promise<Topic[]> {
	const { items } = await apiFetch<{ items: Topic[] }>("/api/personalization/topics");
	return items;
}

export function upsertProfile(body: UpsertProfileBody): Promise<Profile> {
	return apiFetch<Profile>("/api/personalization/me/profile", { method: "PUT", body });
}

// Création : tout envoyer. Mise à jour : seulement les champs modifiés.
export function buildPayload(
	initial: Profile | null,
	values: { name: string; topicIds: string[] },
): UpsertProfileBody {
	const name = values.name.trim();
	if (initial === null) return { name, topic_ids: values.topicIds };

	const payload: UpsertProfileBody = {};
	if (name !== initial.name) payload.name = name;

	const same =
		values.topicIds.length === initial.topic_ids.length &&
		values.topicIds.every((id) => initial.topic_ids.includes(id));
	if (!same) payload.topic_ids = values.topicIds;

	return payload;
}
