import { useOutletContext } from "react-router-dom";
import type { NotificationVariant } from "@/shared/components/Notification";

// Ce que le Layout met à disposition des pages rendues dans son <Outlet />.
export interface LayoutContext {
	notify: (message: string, variant?: NotificationVariant) => void;
}

// Hook à utiliser dans les pages : const { notify } = useLayoutContext();
export function useLayoutContext() {
	return useOutletContext<LayoutContext>();
}
