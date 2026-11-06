import { useEffect, useState } from "react";
import { getBriefing } from "@/features/briefing/api";
import type { Briefing } from "@/features/briefing/types";
import { ApiError } from "@/shared/components/api/client";

export function useBriefing() {
	const [data, setData] = useState<Briefing | null>(null);
	const [savedIds, setSavedIds] = useState<Set<string>>(() => new Set());
	const [isLoading, setIsLoading] = useState(true);
	const [error, setError] = useState<string | null>(null);
	// No profile yet: the page sends the user to the profile form.
	const [profileMissing, setProfileMissing] = useState(false);

	useEffect(() => {
		let active = true;

		async function load() {
			try {
				const response = await getBriefing();

				if (active) {
					setData(response);
					setSavedIds(new Set(response.profile.saved_article_ids));
				}
			} catch (err) {
				if (!active) return;
				if (err instanceof ApiError && err.code === "PROFILE_NOT_FOUND") {
					setProfileMissing(true);
				} else {
					setError("Failed to load your briefing.");
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

	function isSaved(articleId: string) {
		return savedIds.has(articleId);
	}

	// TODO: call POST and DELETE /me/saved-articles/{article_id} (#152).
	// Until then, the change stays in the page and is lost on reload.
	function toggleSave(articleId: string) {
		setSavedIds((prev) => {
			const next = new Set(prev);
			if (next.has(articleId)) next.delete(articleId);
			else next.add(articleId);
			return next;
		});
	}

	return { data, isLoading, error, profileMissing, isSaved, toggleSave };
}
