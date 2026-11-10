import { useState } from "react";
import { Navigate } from "react-router-dom";
import { Division } from "@/shared/components/Division";
import { Text } from "@/shared/components/Text";
import { Tabs, type TabItem } from "@/shared/components/Tab";
import { ArticleCard } from "@/shared/components/ArticleCard";
import { ArticleModal, type Article } from "@/shared/components/ArticleModal";
import { Spinner } from "@/shared/components/Spinner";
import { useBriefing } from "@/features/briefing/hooks/useBriefing";
import type { TopicCluster } from "@/features/briefing/types";
import { toArticle, topicLabel } from "@/shared/utils/article";

interface TopicPanelProps {
	cluster: TopicCluster;
	isSaved: (id: string) => boolean;
	onToggleSave: (id: string) => void;
	onReadMore: (article: Article) => void;
}

interface DashboardHeaderProps {
	firstName: string;
	today: Date;
}

interface TopicSectionProps {
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
		<header className="grid grid-cols-1 gap-6 lg:grid-cols-[minmax(240px,0.9fr)_minmax(0,2.6fr)]">
			<Division
				variant="dashboardcard"
				className="relative min-h-60 justify-between overflow-hidden p-8 after:absolute after:right-10 after:top-10 after:size-10 after:rounded-full after:border-2 after:border-primary after:shadow-[0_0_0_10px_#c981271c] after:content-[''] lg:min-h-[340px] lg:p-12"
			>
				<Text variant="label" className="text-primary">
					Today
				</Text>
				<Text
					variant="subheading"
					className="mt-auto max-w-[12ch] font-serif! text-[clamp(2rem,3.4vw,3.5rem)]! font-medium leading-tight text-accent!"
				>
					{formatDate(today)}
				</Text>
			</Division>

			{/* min-w-0: a grid item can shrink below its content, so a long name can't widen the card. */}
			<Division
				variant="dashboardcard"
				className="min-h-60 min-w-0 justify-between p-8 lg:min-h-[340px] lg:p-12"
			>
				{/* Only the name shrinks and ends with "…"; the full name shows on hover. */}
				<Text
					variant="title"
					className="flex font-serif text-[clamp(2.7rem,4.2vw,5rem)]! leading-[1.1] font-semibold tracking-[-0.055em] text-accent!"
				>
					<span className="shrink-0 whitespace-pre">{"Good morning "}</span>
					<span className="min-w-0 truncate pb-1" title={firstName}>
						{firstName}
					</span>
					<span className="shrink-0">!</span>
				</Text>
				<Text
					variant="lead"
					className="max-w-3xl font-sans! text-lg font-normal not-italic leading-relaxed text-[#7b6b62]! lg:text-2xl"
				>
					"The best way to predict the future is to invent it." - Alan Kay
				</Text>
			</Division>
		</header>
	);
}

function TopicPanel({ cluster, isSaved, onToggleSave, onReadMore }: TopicPanelProps) {
	const articles = cluster.articles.map(toArticle);

	let stories;
	if (articles.length > 0) {
		stories = (
			<div className="grid grid-cols-1 gap-6 md:grid-cols-2 xl:grid-cols-3">
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
		<div className="flex flex-col gap-9">
			<Division variant="dashboardcard" className="min-h-44 justify-center gap-4 p-8 lg:p-10">
				<Text
					variant="subheading"
					className="font-serif! text-[clamp(1.45rem,2vw,2.1rem)]! font-semibold tracking-tight text-accent!"
				>
					Summary of {topicLabel(cluster.topic_id)} today
				</Text>
				<Text variant="body" className="text-lg text-[#7b6b62]">
					{cluster.summary ?? "The summary of this topic is not ready yet."}
				</Text>
			</Division>

			<section className="flex flex-col gap-6">
				<div>
					<Text
						variant="subheading"
						className="font-serif! text-[clamp(1.9rem,2.5vw,2.6rem)]! font-semibold tracking-tight text-accent!"
					>
						Stories to know
					</Text>
					<Text variant="body" className="text-[#7b6b62]">
						Curated from your trusted sources
					</Text>
				</div>

				{stories}
			</section>
		</div>
	);
}

function TopicSection({ tabs }: TopicSectionProps) {
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
		<section className="flex flex-col gap-5">
			<Text
				variant="subheading"
				className="font-serif! text-[clamp(1.9rem,2.5vw,2.6rem)]! font-semibold tracking-tight text-accent!"
			>
				Your interests
			</Text>
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
			<TopicPanel
				cluster={cluster}
				isSaved={isSaved}
				onToggleSave={(id) => {
					void toggleSave(id);
				}}
				onReadMore={setSelectedArticle}
			/>
		),
	}));

	return (
		<Division variant="dashboardpage" className="max-w-none gap-10">
			<DashboardHeader firstName={data.profile.name} today={today} />
			<TopicSection tabs={tabs} />
			<ArticleModal article={selectedArticle} onClose={() => setSelectedArticle(null)} />
		</Division>
	);
}
