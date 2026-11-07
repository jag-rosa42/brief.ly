import { Navigate, useNavigate } from "react-router-dom";
import { type TabItem } from "@/shared/components/Tab";
import { SavedArticles } from "@/pages/SavedArticlesPage";
import { BriefPage } from "@/pages/BriefPage";
import { ProfilePage } from "@/pages/ProfilePage";
import { Sidebar } from "@/shared/components/Sidebar";
import { PublicApiKeyPage } from "@/pages/PublicApiKeyPage";
import type { DashboardTab } from "@/app/navigation";
import { useLogout } from "@/app/useLogout";
import { useProfile } from "@/app/useProfile";
import { Text } from "@/shared/components/Text";
import { Button } from "@/shared/components/Button";
import { Division } from "@/shared/components/Division";

const tabs: (TabItem & { value: DashboardTab })[] = [
	{ value: "brief", label: "Morning Briefing" },
	{ value: "profile", label: "Profile" },
	{ value: "saved", label: "Saved Articles" },
	{ value: "publicapikey", label: "Public API key" },
];

export function DashboardPage({ tab: activeTab }: { tab: DashboardTab }) {
	const navigate = useNavigate();
	const logout = useLogout();
	const { isProfileComplete, loading, error, reload } = useProfile();

	if (loading) {
		return (
			<Division variant="dashboardpage" className="items-center">
				<Text variant="body">Loading...</Text>
			</Division>
		);
	}
	if (error) {
		return (
			<Division variant="dashboardpage" className="items-center">
				<Text variant="error" role="alert">
					{error}
				</Text>
				<Button variant="secondary" onClick={() => void reload()}>
					Retry
				</Button>
			</Division>
		);
	}

	if (!isProfileComplete && activeTab !== "profile") {
		return <Navigate to="/dashboard/profile" replace />;
	}

	const visibleTabs = tabs.map((tab) => ({
		...tab,
		disabled: !isProfileComplete && tab.value !== "profile",
	}));

	return (
		<div className="bg-background min-h-screen flex">
			<Sidebar
				tabs={visibleTabs}
				activeTab={activeTab}
				onSelectTab={(value) => void navigate(`/dashboard/${value}`)}
				onDisconnect={() => {
					void logout();
				}}
			/>
			<main className="flex-1 min-w-0 p-8">
				{activeTab === "brief" && <BriefPage />}
				{activeTab === "profile" && <ProfilePage />}
				{activeTab === "saved" && <SavedArticles />}
				{activeTab === "publicapikey" && <PublicApiKeyPage />}
			</main>
		</div>
	);
}
