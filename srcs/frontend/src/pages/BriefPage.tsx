import { useRef, useState } from "react";
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
import { Button } from "@/shared/components/Button";
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

function getGreeting(date: Date): string {
	const hour = date.getHours();

	if (hour < 12) {
		return "Good morning";
	}
	if (hour < 18) {
		return "Good afternoon";
	}
	return "Good evening";
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

			{/* min-w-0: a grid item can shrink below its content, so a long name can't widen the card. */}
			<Division variant="dashboardcard" className="min-w-0 md:col-span-2">
				{/* Only the name shrinks and ends with "…"; the full name shows on hover. */}
				<Text variant="title" className="flex font-serif">
					<span className="shrink-0 whitespace-pre">{`${getGreeting(today)} `}</span>
					<span className="min-w-0 truncate pb-1" title={firstName}>
						{firstName}
					</span>
					<span className="shrink-0">!</span>
				</Text>
				<Text variant="lead" className="italic text-accent/80">
					"The best way to predict the future is to invent it." - Alan Kay
				</Text>
			</Division>
		</header>
	);
}

function TopicPanel({ cluster, isSaved, onToggleSave, onReadMore }: TopicPanelProps) {
	const scrollRef = useRef<HTMLDivElement>(null);
	const articles = cluster.articles.map(toArticle);

	function scrollByCard(direction: 1 | -1) {
		scrollRef.current?.scrollBy({ left: direction * 344, behavior: "smooth" });
	}
	let stories;
	if (articles.length > 0) {
		stories = (
			<div
				ref={scrollRef}
				className="flex gap-6 overflow-x-auto snap-x snap-mandatory px-1 pt-1 pb-4"
			>
				{articles.map((article) => (
					<div key={article.id} className="flex w-80 shrink-0 snap-start">
						<ArticleCard
							article={article}
							isSaved={isSaved(article.id)}
							onReadMore={() => onReadMore(article)}
							onToggleSave={() => onToggleSave(article.id)}
						/>
					</div>
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
				<div className="flex items-end justify-between gap-4">
					<div>
						<Text variant="subheading">Stories to know</Text>
						<Text variant="body" className="text-info">
							Curated from your trusted sources
						</Text>
					</div>
					{articles.length > 0 && (
						<div className="flex gap-2">
							<Button
								type="button"
								variant="primary"
								aria-label="Previous stories"
								onClick={() => scrollByCard(-1)}
							>
								←
							</Button>
							<Button
								type="button"
								variant="primary"
								aria-label="Next stories"
								onClick={() => scrollByCard(1)}
							>
								→
							</Button>
						</div>
					)}
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

	return <section className="mt-4 flex flex-col gap-4">{content}</section>;
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
		<Division variant="dashboardpage" className="max-w-6xl gap-8">
			<DashboardHeader firstName={data.profile.name} today={today} />
			<TopicSection tabs={tabs} />
			<ArticleModal article={selectedArticle} onClose={() => setSelectedArticle(null)} />
		</Division>
	);
}
