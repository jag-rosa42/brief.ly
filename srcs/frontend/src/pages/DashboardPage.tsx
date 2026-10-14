import { useState } from "react";
import { Division } from "@/shared/components/Division";
import { Text } from "@/shared/components/Text";
import { Tabs, type TabItem } from "@/shared/components/Tab";
import { ArticleCard } from "@/shared/components/ArticleCard";
import { ArticleModal, type Story } from "@/shared/components/ArticleModal";
import { useDashboardData } from "@/utils/useDashboardData";
import { useSavedArticles } from "@/app/SavedArticlesContext";

const days = [
	"Sunday",
	"Monday",
	"Tuesday",
	"Wednesday",
	"Thursday",
	"Friday",
	"Saturday",
];

const months = [
	"January",
	"February",
	"March",
	"April",
	"May",
	"June",
	"July",
	"August",
	"September",
	"October",
	"November",
	"December",
];

function formatDate(date: Date) {
	const weekday = days[date.getDay()];
	const day = date.getDate();
	const month = months[date.getMonth()];
	const year = date.getFullYear();

	return(`${weekday}, ${day} ${month} ${year}`);
}

export function DashboardPage() {
	//TODO: API call to get Dashboard data: connect
	const { data, isLoading, error } = useDashboardData();
	const [selectedStory, setSelectedStory] = useState<Story | null>(null);

	// TODO: call API here to get the saved articles' ids
	const { isSaved, toggleSave } = useSavedArticles();

	function buildTabs(): TabItem[] {
		if (!data)
			return ([]);
		return (data.preferences.map((pref) => ({
			value: pref.id,
			label: pref.name,
			content: (
				<div className="flex flex-col gap-8">
					<Division variant="dashboardcard">
								<Text variant="subheading">
									Summary of {pref.name} today
								</Text>
								<Text variant="body" className="text-accent/80">
									{pref.summary}
								</Text>

					</Division>

					<div className="flex flex-col gap-4">
						<div>
							<Text variant="subheading">Stories to know</Text>
							<Text variant="body" className="text-info">
								Curated from your trusted sources
							</Text>
						</div>

						<div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
							{pref.stories.map((story) => (
								<ArticleCard
									key={story.id}
									story={story}
									isSaved={isSaved(story.id)}
									onReadMore={() => setSelectedStory(story)}
									onToggleSave={() => toggleSave(story.id)}
								/>
							))}
						</div>
					</div>
				</div>
			),
		})));
	}
	const tabs = buildTabs();

	if (isLoading) {
		const loadingMessage = (
			<Text variant="body">
			Loading your brief…
				</Text>
		);
		return (loadingMessage);
	}

	if (error || !data) {
		const errorMessage = (
		<Text variant="body">
			Something went wrong. Please try again.
			</Text>
		);
		return (errorMessage);
	}

	let preferenceSection;
	if (tabs.length > 0) {
		preferenceSection = <Tabs tabs={tabs} variant="pill"/>;
	} else {
		preferenceSection = (
			<Division variant="dashboardcard">
				<Text variant="body">
					You haven't selected any preferences yet. Complete your profile to get your personalised brief.
				</Text>
			</Division>
		);
	}

	return (
		<div className="min-h-screen bg-background p-4 md:p-8">
			<div className="mx-auto flex w-full max-w-6xl flex-col gap-8">
				<div className="grid grid-cols-1 gap-6 md:grid-cols-3">
					<Division variant="dashboardcard">
						<Text
							variant="body"
							className="text-[11px] font-semibold uppercase tracking-wider text-info"
						>
							Today
						</Text>
						<Text variant="subheading">
							{formatDate(new Date())}
						</Text>
					</Division>

					<Division variant="dashboardcard" className="md:col-span-2">
						<Text variant="title" className="font-serif">
							Good morning {data.user.firstName}!
						</Text>
						<Text variant="lead" className="italic text-accent/80">
							"The best way to predict the future is to invent it." - Alan Kay
						</Text>
					</Division>
				</div>

				<div className="mt-4 flex flex-col gap-4">
					<div>
						<Text variant="subheading">Your interests</Text>
					</div>
					{preferenceSection}
				</div>
				<ArticleModal
					story={selectedStory}
					onClose={() => setSelectedStory(null)}
				/>
			</div>
		</div>
	);
}