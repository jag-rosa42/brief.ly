import { createContext, useContext, useState } from "react";
import type { ReactNode } from "react";

interface PreferencesContextValue {
	selectedPreferences: string[];
	updatePreferences: (preferences: string[]) => void;
}

const PreferencesContext = createContext<PreferencesContextValue | undefined>(undefined);

interface PreferencesProviderProps {
	children: ReactNode;
}

export function PreferencesProvider({
	children,
}: PreferencesProviderProps) {
	//TODO: API call to get user's preferences
	const [selectedPreferences, setSelectedPreferences] = useState<string[]>([]);

	function updatePreferences(preferences: string[]) {
		//TODO: API calls to save the user's preferences
		setSelectedPreferences(preferences);
	}

	return (
		<PreferencesContext.Provider
			value={{ selectedPreferences, updatePreferences }}
		>
			{children}
		</PreferencesContext.Provider>
	);
}

export function usePreferences() {
	const context = useContext(PreferencesContext);

	if (context === undefined) {
		throw new Error(
			"usePreferences must be used within a PreferencesProvider"
		);
	}

	return context;
}