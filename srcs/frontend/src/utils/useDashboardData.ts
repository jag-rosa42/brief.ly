import { MOCK_DASHBOARD, type DashboardData } from "@/utils/mock";

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
	return { data: MOCK_DASHBOARD, isLoading: false, error: null };
}