import { createContext, useContext, useState } from "react";
import type { ReactNode } from "react";

interface SavedArticlesContextValue {
	savedIds: Set<string>;
	isSaved: (id: string) => boolean;
	toggleSave: (id:string) => void;
}

const SavedArticlesContext = createContext<SavedArticlesContextValue | undefined>(undefined);

interface SavedArticlesProviderProps {
	children: ReactNode;
}

export function SavedArticlesProvider({ children }: SavedArticlesProviderProps) {
	//TODO: API call to get the saved artilces' ids
	const [savedIds, setSavedIds] = useState<Set<string>>(() => new Set());
	function isSaved(id: string) {
		return savedIds.has(id);
	}
	function toggleSave(id: string) {
		//TODO: API call to save/delete the article
		setSavedIds((prev) => {
			const next = new Set(prev);
			if (next.has(id))
				next.delete(id);
			else
				next.add(id);
			return (next);
		}); 
	}
	return (
		<SavedArticlesContext.Provider value={{ savedIds, isSaved, toggleSave}}>
			{children}
		</SavedArticlesContext.Provider>
	);
}

export function useSavedArticles() {
	const context = useContext(SavedArticlesContext);
	if (context === undefined) {
		throw new Error("useSavedArticles must be used within a SavedArticlesProvider");
	}
	return (context);
}