import { useState } from "react";
import { Sidebar, type SidebarTab } from "@/shared/components/Sidebar";
import { Text } from "@/shared/components/Text";
import { SavedArticles } from "@/pages/SavedArticles";


const tabs: SidebarTab[] = [
	{ id: "brief", label: "Brief" },
	{ id: "preferences", label: "Preferences" },
	{ id: "saved", label: "Saved Articles" },
];

export function SidebarTestPage() {
	const [activeTab, setActiveTab] = useState("brief");
	const [disconnectClicks, setDisconnectClicks] = useState(0);

	return (
		<div className="bg-background min-h-screen flex">
			<Sidebar
				tabs={tabs}
				activeTab={activeTab}
				onSelectTab={setActiveTab}
				onDisconnect={() => setDisconnectClicks(disconnectClicks + 1)}
			/>
			{activeTab === "saved" && <SavedArticles />}

		</div>
	);
}
