import { useAuth } from "@/app/AuthContext";
import { Navigate, useNavigate, useParams } from "react-router-dom";
import { Sidebar, type SidebarTab } from "@/shared/components/Sidebar";
import { SavedArticles } from "@/pages/SavedArticlesPage";
import { DashboardPage } from "./DashboardPage";
import { PreferencesPage } from "./PreferencesPage";


const tabs: SidebarTab[] = [
	{ id: "brief", label: "Morning Briefing" },
	{ id: "preferences", label: "Preferences" },
	{ id: "saved", label: "Saved Articles" },
];

export function SidebarPage() {
	const navigate = useNavigate();
	const { tab: activeTab = "brief" } = useParams();
	const { profileComplete, logout } = useAuth();

	if (!profileComplete && activeTab !== "preferences") {
		return <Navigate to="/sidebar/preferences" replace />;
  }

const visibleTabs = tabs.map((tab) => ({
	...tab,
	disabled: !profileComplete && tab.id !== "preferences",
}));

	return (
		<div className="bg-background min-h-screen flex">
			<Sidebar
				tabs={visibleTabs}
				activeTab={activeTab}
				onSelectTab={(id) => navigate(`/sidebar/${id}`)}
				onDisconnect={() =>{
					logout();
				}}
			/>
			<main className="flex-1 min-w-0 flex-col items-center p-8">
				{activeTab === "brief" && <DashboardPage />}
				{activeTab === "preferences" && <PreferencesPage />}
				{activeTab === "saved" && <SavedArticles />}
			</main>
		</div>
	);
}