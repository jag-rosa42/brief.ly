import { useState } from "react";
import type { ReactNode } from "react";
import { SavedArticlesContext } from "@/app/SavedArticlesContextDefinition";

interface SavedArticlesProviderProps {
	children: ReactNode;
}

export function SavedArticlesProvider({ children }: SavedArticlesProviderProps) {
	const [savedIds, setSavedIds] = useState<Set<string>>(() => new Set());
	function isSaved(id: string) {
		return savedIds.has(id);
	}
	function toggleSave(id: string) {
		setSavedIds((prev) => {
			const next = new Set(prev);
			if (next.has(id)) next.delete(id);
			else next.add(id);
			return next;
		});
	}
	return (
		<SavedArticlesContext value={{ savedIds, isSaved, toggleSave }}>
			{children}
		</SavedArticlesContext>
	);
}
