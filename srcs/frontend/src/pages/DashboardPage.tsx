import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "@/app/AuthContext";
import { ProfilePage } from "@/pages/ProfilePage";
import { SavedArticles } from "@/pages/SavedArticles";
import { Sidebar, type SidebarTab } from "@/shared/components/Sidebar";
import { Text } from "@/shared/components/Text";

const tabs: SidebarTab[] = [
	{ id: "brief", label: "Brief" },
	{ id: "preferences", label: "Preferences" },
	{ id: "saved", label: "Saved Articles" },
];

export function DashboardPage() {
	const [activeTab, setActiveTab] = useState("brief");
	const { logout } = useAuth();
	const navigate = useNavigate();

	function handleDisconnect() {
		logout();
		void navigate("/");
	}

	return (
		<div className="bg-background min-h-screen flex">
			<Sidebar
				tabs={tabs}
				activeTab={activeTab}
				onSelectTab={setActiveTab}
				onDisconnect={handleDisconnect}
			/>
			<main role="tabpanel" className="flex-1">
				{/* TODO: remplacer par le vrai contenu du Brief */}
				{activeTab === "brief" && <Text variant="title" className="p-6">Brief</Text>}
				{activeTab === "preferences" && <ProfilePage />}
				{activeTab === "saved" && <SavedArticles />}
			</main>
		</div>
	);
}
