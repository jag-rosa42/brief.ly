import { useEffect, useState } from "react";
import { getProfile, getTopics, updateProfile } from "@/features/profile/api";
import type { Profile, ProfileUpdate, Topic } from "@/features/profile/types";
import { ApiError } from "@/shared/components/api/client";

// The profile is optional: a new user has none yet (404 PROFILE_NOT_FOUND).
async function getProfileOrNull(): Promise<Profile | null> {
	try {
		return await getProfile();
	} catch (err) {
		if (err instanceof ApiError && err.code === "PROFILE_NOT_FOUND") return null;
		throw err;
	}
}

export function useProfile() {
	const [profile, setProfile] = useState<Profile | null>(null);
	const [topics, setTopics] = useState<Topic[]>([]);
	const [isLoading, setIsLoading] = useState(true);
	const [error, setError] = useState<string | null>(null);

	useEffect(() => {
		let active = true;

		async function load() {
			try {
				const [loadedProfile, loadedTopics] = await Promise.all([getProfileOrNull(), getTopics()]);

				if (active) {
					setProfile(loadedProfile);
					setTopics(loadedTopics.items);
				}
			} catch {
				if (active) {
					setError("Failed to load your profile.");
				}
			} finally {
				if (active) {
					setIsLoading(false);
				}
			}
		}

		void load();

		return () => {
			active = false;
		};
	}, []);

	// Errors are left to the caller, which shows them in the form.
	async function save(update: ProfileUpdate) {
		const saved = await updateProfile(update);
		setProfile(saved);
		return saved;
	}

	return { profile, topics, isLoading, error, save };
}
