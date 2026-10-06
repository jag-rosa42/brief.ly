import { useEffect } from "react";

export const notificationVariants = ["info", "success", "error"] as const;
export type NotificationVariant = typeof notificationVariants[number];

export function getNotificationStyle(variant: NotificationVariant): string
{
	switch(variant) {
		case "info":
			return("bg-background-light border-info text-accent");
		case "success":
			return("bg-background-light border-success text-success");
		case "error":
			return("bg-background-light border-error text-error");
	}
}

interface NotificationProps {
	message: string;
	variant?: NotificationVariant;
	duration?: number;
	onClose: () => void;
}

export function Notification({
	message,
	variant = "info",
	duration = 4000,
	onClose,
}: NotificationProps) {
	const style = getNotificationStyle(variant);

	useEffect(() => {
		const timer = setTimeout(onClose, duration);
		return () => clearTimeout(timer);
	}, [duration, onClose]);

	return (
		<div
			role="status"
			className={`fixed bottom-4 right-4 z-50 max-w-sm rounded-lg border-l-4 px-4 py-3 pr-10 shadow-lg ${style}`}
		>
			<p>{message}</p>
			<button
				type="button"
				aria-label="Fermer la notification"
				onClick={onClose}
				className="absolute top-2 right-2 text-info hover:text-accent"
			>
				✕
			</button>
		</div>
	);
}
