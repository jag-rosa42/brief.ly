export const notificationVariants = ["info", "success", "error"] as const;
export type NotificationVariant = (typeof notificationVariants)[number];

export function getNotificationStyle(variant: NotificationVariant): string {
	switch (variant) {
		case "info":
			return "bg-background-light border-info text-accent";
		case "success":
			return "bg-background-light border-success text-success";
		case "error":
			return "bg-background-light border-error text-error";
	}
}
