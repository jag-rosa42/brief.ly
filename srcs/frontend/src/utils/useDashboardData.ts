import { MOCK_DASHBOARD, type DashboardData } from "@/utils/mock";
import { useProfile } from "@/app/useProfile";

interface UseDashboardData {
	data: DashboardData | null;
	isLoading: boolean;
	error: string | null;
}

// Dashboard data is currently mocked.
// User preferences are retrieved from the real Personalization profile
// and used to filter the mock preferences.
// TODO: replace MOCK_DASHBOARD with real API data

export function useDashboardData(): UseDashboardData {
	const { profile } = useProfile();
	let selectedPreferences: string[] = [];

	if (profile?.topic_ids) {
		selectedPreferences = profile.topic_ids;
	}

	const data: DashboardData = {
		...MOCK_DASHBOARD,
		preferences: MOCK_DASHBOARD.preferences.filter((pref) => selectedPreferences.includes(pref.id)),
	};

	return { data, isLoading: false, error: null };
}
