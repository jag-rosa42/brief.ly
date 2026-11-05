import { useState } from "react";
import type { ReactNode } from "react";

import { PreferencesContext } from "@/app/PreferencesContextDefinition";

interface PreferencesProviderProps {
	children: ReactNode;
}

export function PreferencesProvider({ children }: PreferencesProviderProps) {
	//TODO: API call to get user's preferences
	const [selectedPreferences, setSelectedPreferences] = useState<string[]>([]);

	function updatePreferences(preferences: string[]) {
		//TODO: API calls to save the user's preferences
		setSelectedPreferences(preferences);
	}

	return (
		<PreferencesContext value={{ selectedPreferences, updatePreferences }}>
			{children}
		</PreferencesContext>
	);
}
