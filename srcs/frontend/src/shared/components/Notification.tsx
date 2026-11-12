import { useEffect } from "react";
import {
	getNotificationStyle,
	type NotificationVariant,
} from "@/shared/components/notificationVariants";
import { Icon } from "@/shared/components/Icon";

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
			// An error must be read out right away: it disappears after a few seconds.
			role={variant === "error" ? "alert" : "status"}
			className={`fixed bottom-4 left-4 right-4 z-50 rounded-lg sm:left-auto sm:max-w-sm border-l-4 px-4 py-3 pr-10 shadow-lg ${style}`}
		>
			<p>{message}</p>
			<button
				type="button"
				aria-label="Close notification"
				onClick={onClose}
				className="absolute top-2 right-2 text-info hover:text-accent"
			>
				<Icon name="close" size="sm" />
			</button>
		</div>
	);
}
