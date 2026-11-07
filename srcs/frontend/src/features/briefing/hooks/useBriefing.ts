import { useEffect, useState, useRef } from "react";
import { getBriefing } from "@/features/briefing/api";
import type { Briefing } from "@/features/briefing/types";
import { ApiError } from "@/shared/components/api/client";
import { deleteSavedArticle, saveArticle } from "@/features/saved-articles/api";

export function useBriefing() {
	const [data, setData] = useState<Briefing | null>(null);
	const [savedIds, setSavedIds] = useState<Set<string>>(() => new Set());
	const pendingIds = useRef(new Set<string>());
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

	async function toggleSave(articleId: string) {
		if (pendingIds.current.has(articleId)) return;

		const wasSaved = isSaved(articleId);

		pendingIds.current.add(articleId);
		try {
			if (wasSaved) {
				await deleteSavedArticle(articleId);
			} else {
				await saveArticle(articleId);
			}
			setSavedIds((prev) => {
				const next = new Set(prev);
				if (wasSaved) next.delete(articleId);
				else next.add(articleId);
				return next;
			});
		} catch {
			// TODO: notify the user that the article could not be saved or removed.
		} finally {
			pendingIds.current.delete(articleId);
		}
	}

	function isSaved(articleId: string) {
		return savedIds.has(articleId);
	}
	return { data, isLoading, error, profileMissing, isSaved, toggleSave };
}
