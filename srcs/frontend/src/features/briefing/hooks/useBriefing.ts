import { useEffect, useState, useRef } from "react";
import { getBriefing } from "@/features/briefing/api";
import type { Briefing } from "@/features/briefing/types";
import { ApiError } from "@/shared/components/api/client";
import { deleteSavedArticle, saveArticle } from "@/features/saved-articles/api";
import { MAX_SAVED_ARTICLES } from "@/features/saved-articles/constants";
import { useNotify } from "@/app/useNotify";


export function useBriefing() {
	const [data, setData] = useState<Briefing | null>(null);
	const [savedIds, setSavedIds] = useState<Set<string>>(() => new Set());
	const pendingIds = useRef(new Set<string>());
	const [isLoading, setIsLoading] = useState(true);
	const [error, setError] = useState<string | null>(null);
	// No profile yet: the page sends the user to the profile form.
	const [profileMissing, setProfileMissing] = useState(false);
	const { notify } = useNotify();

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
			if (wasSaved) notify("The article has been removed from your saved articles.", "success");
			else notify("The article has been added to your saved articles.", "success");
		} catch (err) {
			if (wasSaved) notify("The article could not be removed, please try again.", "error");
			else if (err instanceof ApiError && err.code === "SAVED_ARTICLES_LIMIT_REACHED")
				notify(
					`You can save up to ${MAX_SAVED_ARTICLES} articles: remove one from Saved first.`,
					"error",
				);
			else notify("The article could not be saved, please try again.", "error");
		} finally {
			pendingIds.current.delete(articleId);
		}
	}

	return { data, isLoading, error, profileMissing, isSaved, toggleSave };
}
