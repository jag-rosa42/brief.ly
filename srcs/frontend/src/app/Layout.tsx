import { useState } from "react";
import { Outlet } from "react-router-dom";
import type { LayoutContext } from "@/app/useLayoutContext";
import { Footer } from "@/shared/components/Footer";
import { Header } from "@/shared/components/Header";
import { Notification, type NotificationVariant } from "@/shared/components/Notification";

interface NotificationData {
	message: string;
	variant: NotificationVariant;
}

export function Layout() {
	const [notif, setNotif] = useState<NotificationData | null>(null);

	function notify(message: string, variant: NotificationVariant = "info") {
		setNotif({ message, variant });
	}

	return (
		<div className="bg-background min-h-screen flex flex-col">
			<Header />
			<div className="flex-1"><Outlet context={{ notify } satisfies LayoutContext} /></div>
			<Footer />
			{notif && (
				<Notification
					message={notif.message}
					variant={notif.variant}
					onClose={() => setNotif(null)}
				/>
			)}
		</div>
	);
}
