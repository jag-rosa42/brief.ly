import { useState } from "react";
import { Division } from "@/shared/components/Division";
import { Text } from "@/shared/components/Text";
import { Tabs, type TabItem } from "@/shared/components/Tab";
import { ArticleCard } from "@/shared/components/ArticleCard";
import { ArticleModal, type Article } from "@/shared/components/ArticleModal";
import { useDashboardData } from "@/utils/useDashboardData";
import { useSavedArticles } from "@/app/useSavedArticles";
import { Spinner } from "@/shared/components/Spinner";

interface Preference {
	id: string;
	name: string;
	summary: string;
	articles: Article[];
}

interface PreferencePanelProps {
	preference: Preference;
	isSaved: (id: string) => boolean;
	onToggleSave: (id: string) => void;
	onReadMore: (article: Article) => void;
}

interface DashboardHeaderProps {
	firstName: string;
	today: Date;
}

interface PreferencesSectionProps {
	tabs: TabItem[];
}

function formatDate(date: Date): string {
	return new Intl.DateTimeFormat("en-GB", {
		weekday: "long",
		day: "numeric",
		month: "long",
		year: "numeric",
	}).format(date);
}

function DashboardHeader({ firstName, today }: DashboardHeaderProps) {
	return (
		<header className="grid grid-cols-1 gap-6 md:grid-cols-3">
			<Division variant="dashboardcard">
				<Text variant="label" className="text-info">
					Today
				</Text>
				<Text variant="subheading">{formatDate(today)}</Text>
			</Division>

			<Division variant="dashboardcard" className="md:col-span-2">
				<Text variant="title" className="font-serif">
					Good morning {firstName}!
				</Text>
				<Text variant="lead" className="italic text-accent/80">
					"The best way to predict the future is to invent it." - Alan Kay
				</Text>
			</Division>
		</header>
	);
}

function PreferencePanel({ preference, isSaved, onToggleSave, onReadMore }: PreferencePanelProps) {
	return (
		<div className="flex flex-col gap-8">
			<Division variant="dashboardcard">
				<Text variant="subheading">Summary of {preference.name} today</Text>
				<Text variant="body" className="text-accent/80">
					{preference.summary}
				</Text>
			</Division>

			<section className="flex flex-col gap-4">
				<div>
					<Text variant="subheading">Stories to know</Text>
					<Text variant="body" className="text-info">
						Curated from your trusted sources
					</Text>
				</div>

				<div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
					{preference.articles.map((article) => (
						<ArticleCard
							key={article.id}
							article={article}
							isSaved={isSaved(article.id)}
							onReadMore={() => onReadMore(article)}
							onToggleSave={() => onToggleSave(article.id)}
						/>
					))}
				</div>
			</section>
		</div>
	);
}

function PreferencesSection({ tabs }: PreferencesSectionProps) {
	let content;
	if (tabs.length > 0) {
		content = <Tabs tabs={tabs} variant="pill" />;
	} else {
		content = (
			<Division variant="dashboardcard">
				<Text variant="body">
					You haven't selected any preferences yet. Complete your profile to get your personalised
					brief.
				</Text>
			</Division>
		);
	}

	return (
		<section className="mt-4 flex flex-col gap-4">
			<Text variant="subheading">Your interests</Text>
			{content}
		</section>
	);
}

export function BriefPage() {
	//TODO: API call to get Dashboard data: connect
	const { data, isLoading, error } = useDashboardData();

	const [selectedArticle, setSelectedArticle] = useState<Article | null>(null);
	const [today] = useState(() => new Date());

	// TODO: call API here to get the saved articles' ids
	const { isSaved, toggleSave } = useSavedArticles();

	if (isLoading) {
		return <Spinner />;
	}

	if (error || !data) {
		return (
			<Text variant="body" role="alert">
				Something went wrong. Please try again.
			</Text>
		);
	}
	const tabs: TabItem[] = data.preferences.map((preference) => ({
		value: preference.id,
		label: preference.name,
		content: (
			<PreferencePanel
				preference={preference}
				isSaved={isSaved}
				onToggleSave={toggleSave}
				onReadMore={setSelectedArticle}
			/>
		),
	}));

	return (
		<Division variant="dashboardpage" className="max-w-6x1 gap-8">
			<DashboardHeader firstName={data.user.firstName} today={today} />
			<PreferencesSection tabs={tabs} />
			<ArticleModal article={selectedArticle} onClose={() => setSelectedArticle(null)} />
		</Division>
	);
}
