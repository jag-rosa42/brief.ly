import { useState } from "react";
import { Sidebar, type SidebarTab } from "@/shared/components/Sidebar";
import { SavedArticles } from "@/pages/SavedArticles";
import { DashboardPage } from "./DashboardPage";
import { PreferencesPage } from "./PreferencesPage";


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
			<main className="flex-1 min-w-0 flex-col items-center p-8">
				{activeTab === "brief" && <DashboardPage />}
				{activeTab === "preferences" && <PreferencesPage />}
				{activeTab === "saved" && <SavedArticles />}
			</main>
		</div>
	);
}