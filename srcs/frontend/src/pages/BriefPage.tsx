import { useState } from "react";
import { Navigate } from "react-router-dom";
import { Division } from "@/shared/components/Division";
import { Text } from "@/shared/components/Text";
import { Tabs, type TabItem } from "@/shared/components/Tab";
import { ArticleCard } from "@/shared/components/ArticleCard";
import { ArticleModal, type Article } from "@/shared/components/ArticleModal";
import { Spinner } from "@/shared/components/Spinner";
import { useBriefing } from "@/features/briefing/hooks/useBriefing";
import type { BriefingArticle, TopicCluster } from "@/features/briefing/types";

interface PreferencePanelProps {
	cluster: TopicCluster;
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

// Topic ids are lowercase words ("technologies"): shown with a capital letter.
function topicLabel(topicId: string): string {
	return topicId.charAt(0).toUpperCase() + topicId.slice(1);
}

function toArticle(article: BriefingArticle): Article {
	return {
		id: article.article_id,
		title: article.title,
		summary: article.summary ?? "",
		url: article.url,
		source: article.publisher_name,
		category: topicLabel(article.topic_id),
		readingTime: article.read_time_minutes,
	};
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

function PreferencePanel({ cluster, isSaved, onToggleSave, onReadMore }: PreferencePanelProps) {
	const articles = cluster.articles.map(toArticle);

	let stories;
	if (articles.length > 0) {
		stories = (
			<div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
				{articles.map((article) => (
					<ArticleCard
						key={article.id}
						article={article}
						isSaved={isSaved(article.id)}
						onReadMore={() => onReadMore(article)}
						onToggleSave={() => onToggleSave(article.id)}
					/>
				))}
			</div>
		);
	} else {
		stories = (
			<Text variant="body" className="text-info">
				No story for this topic today.
			</Text>
		);
	}

	return (
		<div className="flex flex-col gap-8">
			<Division variant="dashboardcard">
				<Text variant="subheading">Summary of {topicLabel(cluster.topic_id)} today</Text>
				<Text variant="body" className="text-accent/80">
					{cluster.summary ?? "The summary of this topic is not ready yet."}
				</Text>
			</Division>

			<section className="flex flex-col gap-4">
				<div>
					<Text variant="subheading">Stories to know</Text>
					<Text variant="body" className="text-info">
						Curated from your trusted sources
					</Text>
				</div>

				{stories}
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
	const { data, isLoading, error, profileMissing, isSaved, toggleSave } = useBriefing();

	const [selectedArticle, setSelectedArticle] = useState<Article | null>(null);
	const [today] = useState(() => new Date());

	if (isLoading) {
		return <Spinner />;
	}

	if (profileMissing) {
		return <Navigate to="/dashboard/profile" replace />;
	}

	if (error || !data) {
		return (
			<Text variant="body" role="alert">
				Something went wrong. Please try again.
			</Text>
		);
	}
	const tabs: TabItem[] = data.topic_clusters.map((cluster) => ({
		value: cluster.topic_id,
		label: topicLabel(cluster.topic_id),
		content: (
			<PreferencePanel
				cluster={cluster}
				isSaved={isSaved}
				onToggleSave={toggleSave}
				onReadMore={setSelectedArticle}
			/>
		),
	}));

	return (
		<Division variant="dashboardpage" className="max-w-6x1 gap-8">
			<DashboardHeader firstName={data.profile.name} today={today} />
			<PreferencesSection tabs={tabs} />
			<ArticleModal article={selectedArticle} onClose={() => setSelectedArticle(null)} />
		</Division>
	);
}
