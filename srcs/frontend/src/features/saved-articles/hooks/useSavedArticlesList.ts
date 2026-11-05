import { useEffect, useState } from "react";
import { deleteSavedArticle, getSavedArticles } from "@/features/saved-articles/api";
import type { SavedArticle } from "@/features/saved-articles/types";
import { useNotify } from "@/app/useNotify";

export function useSavedArticlesList() {
	const [data, setData] = useState<SavedArticle[]>([]);
	const [isLoading, setIsLoading] = useState(true);
	const [error, setError] = useState<string | null>(null);
	const { notify } = useNotify();

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
			notify("The article has been removed from your saved articles.", "success");
		} catch {
			notify("The article could not be removed, please try again.", "error");
		}
	}

	return { data, isLoading, error, remove };
}
