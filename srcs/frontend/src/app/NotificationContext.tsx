import { useCallback, useRef, useState } from "react";
import type { ReactNode } from "react";
import { NotificationContext } from "@/app/NotificationContextDefinition";
import { Notification } from "@/shared/components/Notification";
import { type NotificationVariant } from "@/shared/components/notificationVariants";
interface NotificationData {
	id: number;
	message: string;
	variant: NotificationVariant;
}

interface NotificationProviderProps {
	children: ReactNode;
}

export function NotificationProvider({ children }: NotificationProviderProps) {
	const [currentNotification, setCurrentNotification] = useState<NotificationData | null>(null);
	const nextId = useRef(0);

	function notify(message: string, variant: NotificationVariant = "info") {
		nextId.current += 1;
		const newNotification: NotificationData = {
			id: nextId.current,
			message,
			variant,
		};
		setCurrentNotification(newNotification);
	}

	const close = useCallback(() => {
		setCurrentNotification(null);
	}, []);

	return (
		<NotificationContext value={{ notify }}>
			{children}
			{currentNotification && (
				<Notification
					key={currentNotification.id}
					message={currentNotification.message}
					variant={currentNotification.variant}
					onClose={close}
				/>
			)}
		</NotificationContext>
	);
}
