import { createContext } from "react";

export interface SavedArticlesContextValue {
	savedIds: Set<string>;
	isSaved: (id: string) => boolean;
	toggleSave: (id: string) => void;
}

export const SavedArticlesContext = createContext<SavedArticlesContextValue | undefined>(undefined);
