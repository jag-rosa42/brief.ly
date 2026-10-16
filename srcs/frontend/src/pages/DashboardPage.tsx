import { useAuth } from "@/app/useAuth";
import { Navigate, useNavigate, useParams } from "react-router-dom";
import { type TabItem } from "@/shared/components/Tab";
import { SavedArticles } from "@/pages/SavedArticlesPage";
import { BriefPage } from "@/pages/BriefPage";
import { ProfilePage } from "@/pages/ProfilePage";
import { Sidebar } from "@/shared/components/Sidebar";

const tabs: TabItem[] = [
	{ value: "brief", label: "Morning Briefing" },
	{ value: "profile", label: "Profile" },
	{ value: "saved", label: "Saved Articles" },
];

export function DashboardPage() {
	const navigate = useNavigate();
	const { tab: activeTab = "brief" } = useParams();
	const { profileComplete, logout } = useAuth();

	if (!profileComplete && activeTab !== "profile") {
		return <Navigate to="/dashboard/profile" replace />;
  }

const visibleTabs = tabs.map((tab) => ({
	...tab,
	disabled: !profileComplete && tab.value !== "profile",
}));

	return (
		<div className="bg-background min-h-screen flex">
			<Sidebar
				tabs={visibleTabs}
				activeTab={activeTab}
				onSelectTab={
					(value) => void navigate(`/dashboard/${value}`)
				}
				onDisconnect={logout}
			/>
			<main className="flex-1 min-w-0 p-8">
				{activeTab === "brief" && <BriefPage />}
				{activeTab === "profile" && <ProfilePage />}
				{activeTab === "saved" && <SavedArticles />}
			</main>
		</div>
	);
}