import { use } from "react";

import { AuthContext } from "@/app/AuthContextDefinition";

export function useAuth() {
	const context = use(AuthContext);

	if (context === undefined) {
		throw new Error("useAuth must be used within an AuthProvider");
	}
	return context;
}