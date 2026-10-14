import { MOCK_DASHBOARD, type DashboardData } from "@/utils/mock";
import { useMemo } from "react";
import { usePreferences } from "@/app/PreferencesContext";

interface UseDashboardData {
	data: DashboardData | null;
	isLoading: boolean;
	error: string | null;
}

// Aujourd'hui : renvoie les mocks.
// Plus tard : remplace le contenu par un fetch (useState + useEffect) ou
// react-query, en gardant le même retour { data, isLoading, error }.
// DashboardPage n'aura pas besoin de changer.
export function useDashboardData(): UseDashboardData {
		const { selectedPreferences } = usePreferences();

	const data = useMemo<DashboardData>(() => ({
		...MOCK_DASHBOARD,
		preferences: MOCK_DASHBOARD.preferences.filter((pref) =>
			selectedPreferences.includes(pref.id)
		),
	}), [selectedPreferences]);

	return { data, isLoading: false, error: null };
}
