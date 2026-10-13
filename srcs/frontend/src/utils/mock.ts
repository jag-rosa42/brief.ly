import type { Story } from "@/shared/components/ArticleModal";

export interface Preference {
	id: string;
	name: string;
	summary: string;
	stories: Story[];
}

export interface DashboardData {
	user: { firstName: string };
	preferences: Preference[]; 
}

export const MOCK_DASHBOARD: DashboardData = {
	user: { firstName: "Kate" },
	preferences: [
		{
			id: "ai-tech",
			name: "AI & Tech",
			summary:
				"Open-source models keep narrowing the gap with proprietary ones, while infrastructure spending continues to accelerate across Europe and the US.",
			stories: [
				{
					id: "ai-1",
					title: "Open-source models narrow the enterprise gap",
					category: "AI & Tech",
					source: "TechDaily",
					url: "https://example.com/open-source-models",
					summary:
						"Smaller teams gain access to capable models as inference costs continue to fall. Several vendors now offer hosted open-weight models with enterprise-grade guarantees, which changes the build-versus-buy calculation for many companies.",
				},
				{
					id: "ai-2",
					title: "Data centres race to secure clean power",
					category: "AI & Tech",
					source: "Energy Weekly",
					url: "https://example.com/data-centres-power",
					summary:
						"Operators are signing long-term energy contracts as demand from AI workloads grows faster than grid capacity in several regions.",
				},
				{
					id: "ai-3",
					title: "A new benchmark challenges coding assistants",
					category: "AI & Tech",
					source: "Dev Journal",
					url: null,
					summary:
						"Researchers published a benchmark built from real-world pull requests, revealing large differences between assistants on multi-file changes.",
				},
			],
		},
		{
			id: "finance",
			name: "Finance",
			summary:
				"European markets open on a measured note as energy and semiconductor shares lead a quiet rise ahead of the central bank commentary.",
			stories: [
				{
					id: "fin-1",
					title: "European markets open on a measured high",
					category: "Finance",
					source: "Market Wire",
					url: "https://example.com/markets-open",
					summary: "Energy and semiconductor shares lead a quiet rise ahead of central bank commentary.",
				},
				{
					id: "fin-2",
					title: "Bond yields steady before the rate decision",
					category: "Finance",
					source: "Capital Post",
					url: "https://example.com/bond-yields",
					summary: "Investors hold positions as the central bank prepares to announce its next move.",
				},
				{
					id: "fin-3",
					title: "Startups raise less but at higher valuations",
					category: "Finance",
					source: "Venture Notes",
					url: "https://example.com/startup-funding",
					summary: "Funding rounds are fewer this quarter, yet median valuations keep climbing in late-stage deals.",
				},
			],
		},
	],
};