import { useEffect, useState } from "react";
import { deleteSavedArticle, getSavedArticles } from "@/features/saved-articles/api";
import type { SavedArticle } from "@/features/saved-articles/types";

export function useSavedArticlesList() {
	const [data, setData] = useState<SavedArticle[]>([]);
	const [isLoading, setIsLoading] = useState(true);
	const [error, setError] = useState<string | null>(null);

	useEffect(() => {
		let active = true;

		async function load() {
			try {
				const response = await getSavedArticles();

				if (active) {
					setData(response.items);
				}
			} catch {
				if (active) {
					setError("Failed to load saved articles.");
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

	async function remove(articleId: string) {
		try {
			await deleteSavedArticle(articleId);
			setData((prev) => prev.filter((article) => article.article_id !== articleId));
		} catch {
			// TODO: notify the user that the article could not be removed.
		}
	}

	return { data, isLoading, error, remove };
}
