import { use } from "react";

import { ProfileContext } from "@/app/ProfileContextDefinition";

export function useProfile() {
	const context = use(ProfileContext);

	if (context === undefined) {
		throw new Error("useProfile must be used within a ProfileProvider");
	}

	return context;
}
