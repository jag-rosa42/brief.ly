import { useState } from "react";
import { useLayoutContext } from "@/app/useLayoutContext";
import { Button } from "@/shared/components/Button";
import { Link } from "@/shared/components/Link";
import { notificationVariants } from "@/shared/components/Notification";

export function NotificationTestPage() {
	const [message, setMessage] = useState("Ceci est une notification de test");
	const { notify } = useLayoutContext();

	return (
		<div className="min-h-screen flex flex-col gap-4 p-4">
			<h2 className="text-lg font-bold">Notification</h2>

			<label className="flex flex-col gap-1 max-w-md">
				Message
				<input
					className="border rounded px-3 py-2 bg-white"
					value={message}
					onChange={(e) => setMessage(e.target.value)}
				/>
			</label>

			<div className="flex gap-2">
				{notificationVariants.map((variant) => (
					<Button
						key={variant}
						variant="secondary"
						onClick={() => notify(message, variant)}
					>
						{variant}
					</Button>
				))}
			</div>

			<Link to="/designsystem" variant="primary">
				Changer de page (la notification doit rester)
			</Link>
		</div>
	);
}
