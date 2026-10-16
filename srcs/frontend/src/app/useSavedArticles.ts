import { use } from "react";

import { SavedArticlesContext } from "@/app/SavedArticlesContextDefinition";

export function useSavedArticles() {
	const context = use(SavedArticlesContext);
	if (context === undefined) {
		throw new Error("useSavedArticles must be used within a SavedArticlesProvider");
	}
	return (context);
}