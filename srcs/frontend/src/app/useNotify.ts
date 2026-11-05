import { use } from "react";

import { NotificationContext } from "@/app/NotificationContextDefinition";

export function useNotify() {
	const context = use(NotificationContext);
	if (context === undefined) {
		throw new Error("useNotify must be used within a NotificationProvider");
	}
	return context;
}
