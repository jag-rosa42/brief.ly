import { apiFetch } from "@/shared/components/api/client";
import type { SavedArticlesResponse } from "@/features/saved-articles/types";

export function getSavedArticles(): Promise<SavedArticlesResponse> {
	return apiFetch<SavedArticlesResponse>(`/api/personalization/me/saved-articles`);
}

export function deleteSavedArticle(articleId: string): Promise<void> {
	return apiFetch<void>(`/api/personalization/me/saved-articles/${articleId}`, {
		method: "DELETE",
	});
}
