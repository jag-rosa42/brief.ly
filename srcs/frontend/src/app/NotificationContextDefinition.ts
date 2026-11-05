import { createContext } from "react";
import type { NotificationVariant } from "@/shared/components/notificationVariants";

export interface NotificationContextValue {
	notify: (message: string, variant?: NotificationVariant) => void;
}

export const NotificationContext = createContext<NotificationContextValue | undefined>(undefined);
