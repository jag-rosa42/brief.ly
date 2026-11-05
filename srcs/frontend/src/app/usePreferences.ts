import { use } from "react";

import { PreferencesContext } from "@/app/PreferencesContextDefinition";

export function usePreferences() {
	const context = use(PreferencesContext);

	if (context === undefined) {
		throw new Error("usePreferences must be used within a PreferencesProvider");
	}

	return context;
}
