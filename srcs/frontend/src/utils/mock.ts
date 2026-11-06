import type { Article } from "@/shared/components/ArticleModal";

export interface Preference {
	id: string;
	name: string;
	summary: string;
	articles: Article[];
}

export interface DashboardData {
	user: { firstName: string };
	preferences: Preference[];
}

export const MOCK_DASHBOARD: DashboardData = {
	user: { firstName: "Kate" },
	preferences: [
		{
			id: "technology",
			name: "Technology",
			summary:
				"Open-source models keep narrowing the gap with proprietary ones, while infrastructure spending continues to accelerate across Europe and the US.",
			articles: [
				{
					id: "ai-1",
					title: "Open-source models narrow the enterprise gap",
					category: "Technologies",
					source: "TechDaily",
					url: "https://www.aitechdaily.com/",
					summary:
						"Smaller teams gain access to capable models as inference costs continue to fall. Several vendors now offer hosted open-weight models with enterprise-grade guarantees, which changes the build-versus-buy calculation for many companies.",
				},
				{
					id: "ai-2",
					title: "Data centres race to secure clean power",
					category: "Technologies",
					source: "Energy Weekly",
					url: "https://newenergyweekly.co.uk/",
					summary:
						"Operators are signing long-term energy contracts as demand from AI workloads grows faster than grid capacity in several regions.",
				},
				{
					id: "ai-3",
					title: "A new benchmark challenges coding assistants",
					category: "Technologies",
					source: "Dev Journal",
					url: null,
					summary:
						"Researchers published a benchmark built from real-world pull requests, revealing large differences between assistants on multi-file changes.",
				},
			],
		},
		{
			id: "science",
			name: "Science",
			summary:
				"European markets open on a measured note as energy and semiconductor shares lead a quiet rise ahead of the central bank commentary.",
			articles: [
				{
					id: "fin-1",
					title: "European markets open on a measured high",
					category: "Science",
					source: "Market Wire",
					url: "https://example.com/markets-open",
					summary:
						"Energy and semiconductor shares lead a quiet rise ahead of central bank commentary.",
				},
				{
					id: "fin-2",
					title: "Bond yields steady before the rate decision",
					category: "Science",
					source: "Capital Post",
					url: "https://example.com/bond-yields",
					summary:
						"Investors hold positions as the central bank prepares to announce its next move.",
				},
				{
					id: "fin-3",
					title: "Startups raise less but at higher valuations",
					category: "Science",
					source: "Venture Notes",
					url: "https://example.com/startup-funding",
					summary:
						"Funding rounds are fewer this quarter, yet median valuations keep climbing in late-stage deals.",
				},
			],
		},
		{
			id: "business",
			name: "Business",
			summary: "Insert a business summary",
			articles: [
				{
					id: "b-1",
					title: "European businesses accelerate their investment in AI",
					category: "Business",
					source: "Market Wire",
					url: "https://example.com/european-business-ai",
					summary:
						"Companies across Europe are allocating more resources to artificial intelligence, hoping to improve productivity, automate routine tasks and develop new services.",
				},
			],
		},
		{
			id: "entertainment",
			name: "Entertainment",
			summary:
				"Streaming platforms are experimenting with new formats, while independent filmmakers attract growing audiences through innovative storytelling.",
			articles: [
				{
					id: "ent-1",
					title: "Independent films find new audiences through streaming",
					category: "Entertainment",
					source: "Screen Weekly",
					url: "https://example.com/independent-films-streaming",
					summary:
						"Independent filmmakers are reaching international audiences through streaming platforms, opening up new opportunities for productions that might otherwise struggle to secure theatrical distribution.",
				},
			],
		},
		{
			id: "general",
			name: "General",
			summary:
				"Cities are investing in greener public spaces and more efficient transport networks as communities look for practical ways to improve everyday life.",
			articles: [
				{
					id: "gen-1",
					title: "Cities rethink public spaces to improve everyday life",
					category: "General",
					source: "The Daily Report",
					url: "https://example.com/cities-public-spaces",
					summary:
						"Urban planners are redesigning public spaces with more trees, pedestrian areas and accessible facilities to make neighbourhoods more comfortable and sustainable.",
				},
			],
		},
		{
			id: "health",
			name: "Health",
			summary:
				"Public health researchers are investigating how sleep quality, physical activity and everyday habits influence long-term wellbeing.",
			articles: [
				{
					id: "hea-1",
					title: "Researchers examine the link between sleep and long-term health",
					category: "Health",
					source: "Health Monitor",
					url: "https://example.com/sleep-long-term-health",
					summary:
						"Researchers are studying how sleep duration and consistency relate to physical and cognitive health, highlighting the importance of regular sleep routines.",
				},
			],
		},
		{
			id: "sports",
			name: "Sports",
			summary:
				"Sports teams are exploring new training methods and performance analytics, while young athletes continue to make their mark in international competitions.",
			articles: [
				{
					id: "spo-1",
					title: "Performance analytics reshape modern sports training",
					category: "Sport",
					source: "Sports Journal",
					url: "https://example.com/sports-performance-analytics",
					summary:
						"Coaches are using performance data to analyse player workloads, refine training sessions and identify opportunities to improve team performance throughout the season.",
				},
			],
		},
	],
};
