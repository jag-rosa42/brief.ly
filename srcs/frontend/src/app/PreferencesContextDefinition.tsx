import { createContext } from "react";

export interface PreferencesContextValue {
	selectedPreferences: string[];
	updatePreferences: (preferences: string[]) => void;
}

export const PreferencesContext = createContext<PreferencesContextValue | undefined>(undefined);
