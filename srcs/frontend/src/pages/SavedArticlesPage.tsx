import { useState } from "react";
import { useDashboardData } from "@/utils/useDashboardData";
import { useSavedArticles } from "@/app/useSavedArticles";
import { Button } from "@/shared/components/Button";
import { ArticleCard } from "@/shared/components/ArticleCard";
import { ArticleModal, type Story } from "@/shared/components/ArticleModal";
import { Dropdown } from "@/shared/components/Dropdown";
import { Input } from "@/shared/components/Input";
import { Text } from "@/shared/components/Text";
import { Division } from "@/shared/components/Division"

const ARTICLES_PER_PAGE = 4;
const DEFAULT_READING_TIME = 4;

const ORDER_OPTIONS = [
	{ value: "asc", label: "Shortest first" },
	{ value: "desc", label: "Longest first" },
];

// Renvoie les valeurs sans doublon, précédées de l'option "tout afficher".
function buildOptions(values: string[], allLabel: string) {
	const uniqueValues = [...new Set(values)];
	return [
		{ value: "all", label: allLabel },
		...uniqueValues.map((value) => ({ value, label: value })),
	];
}

function getSavedArticles(stories: Story[], savedIds: Set<string>): Story[] {
	const uniqueStories = new Map(stories.map((story) => [story.id, story] as const));
	return [...uniqueStories.values()].filter((story) => savedIds.has(story.id));
}

interface FilterValues {
	search: string;
	source: string;
	topic: string;
}

function filterArticles(articles: Story[], { search, source, topic }: FilterValues): Story[] {
	const keywords = search.toLowerCase().split(" ").filter((word) => word !== "");

	return articles.filter((article) => {
		const content = `${article.title} ${article.summary}`.toLowerCase();
		const matchesSearch = keywords.every((word) => content.includes(word));
		const matchesSource = source === "all" || article.source === source;
		const matchesTopic = topic === "all" || article.category === topic;
		return matchesSearch && matchesSource && matchesTopic;
	});
}

function sortByReadingTime(articles: Story[], order: string): Story[] {
	const sortedArticles = [...articles];

	sortedArticles.sort((a, b) => {
		let timeA = a.readingTime;
		let timeB = b.readingTime;

		timeA ??= DEFAULT_READING_TIME;
  		timeB ??= DEFAULT_READING_TIME;

		if (order === "asc") {
			return timeA - timeB;
		} else {
			return timeB - timeA;
		}
	});

	return sortedArticles;
}

interface SavedArticlesFiltersProps {
	articles: Story[];
	search: string;
	source: string;
	topic: string;
	order: string;
	onSearchChange: (value: string) => void;
	onSourceChange: (value: string) => void;
	onTopicChange: (value: string) => void;
	onOrderChange: (value: string) => void;
}

function SavedArticlesFilters({
	articles,
	search,
	source,
	topic,
	order,
	onSearchChange,
	onSourceChange,
	onTopicChange,
	onOrderChange,
}: SavedArticlesFiltersProps) {
	return (
		<div className="flex flex-wrap items-end gap-4">
			<Input
				name="search"
				label="Search"
				variant="sub"
				placeholder="Keywords..."
				value={search}
				onChange={(e) => onSearchChange(e.target.value)}
			/>
			<Dropdown
				name="source"
				label="Source"
				variant="main"
				options={buildOptions(articles.map((article) => article.source), "All sources")}
				value={source}
				onChange={(e) => onSourceChange(e.target.value)}
			/>
			<Dropdown
				name="topic"
				label="Topic"
				variant="main"
				options={buildOptions(articles.map((article) => article.category), "All topics")}
				value={topic}
				onChange={(e) => onTopicChange(e.target.value)}
			/>
			<Dropdown
				name="order"
				label="Reading time"
				variant="main"
				options={ORDER_OPTIONS}
				value={order}
				onChange={(e) => onOrderChange(e.target.value)}
			/>
		</div>
	);
}

interface PaginationProps {
	currentPage: number;
	pageCount: number;
	onPageChange: (page: number) => void;
}

function Pagination({ currentPage, pageCount, onPageChange }: PaginationProps) {
	return (
		<div className="flex items-center justify-center gap-4">
			<Button variant="primary" disabled={currentPage === 1} onClick={() => onPageChange(currentPage - 1)}>
				🡨
			</Button>
			<Text variant="body">Page {currentPage} / {pageCount}</Text>
			<Button variant="primary" disabled={currentPage === pageCount} onClick={() => onPageChange(currentPage + 1)}>
				🡪
			</Button>
		</div>
	);
}

export function SavedArticles() {
	const { data } = useDashboardData();
	const { savedIds, toggleSave } = useSavedArticles();

	const [search, setSearch] = useState("");
	const [source, setSource] = useState("all");
	const [topic, setTopic] = useState("all");
	const [order, setOrder] = useState("asc");
	const [page, setPage] = useState(1);
	const [openedArticle, setOpenedArticle] = useState<Story | null>(null);

	// TODO: remplacer par l'appel API qui renvoie les articles sauvegardés.
	let allStories: Story[] = [];
	if (data) {
		allStories = data.preferences.flatMap((pref) => {
			return (pref.stories);
		});
	}
	const articles = getSavedArticles(allStories, savedIds);
	const filteredArticles = filterArticles(articles, { search, source, topic });
	const sortedArticles = sortByReadingTime(filteredArticles, order);

	const pageCount = Math.max(1, Math.ceil(sortedArticles.length / ARTICLES_PER_PAGE));
	// Si la dernière page se vide (article retiré), on recule sur la dernière page existante.
	const currentPage = Math.min(page, pageCount);
	const firstIndex = (currentPage - 1) * ARTICLES_PER_PAGE;
	const visibleArticles = sortedArticles.slice(firstIndex, firstIndex + ARTICLES_PER_PAGE);

	// Quand un filtre change, on revient à la première page.
	function changeFilter(setFilter: (value: string) => void, value: string) {
		setFilter(value);
		setPage(1);
	}

	return (
		<Division variant="dashboardpage" className="max-w-4xl gap-6">
			<Text variant="title">Saved Articles</Text>
			<SavedArticlesFilters
				articles={articles}
				search={search}
				source={source}
				topic={topic}
				order={order}
				onSearchChange={(value) => changeFilter(setSearch, value)}
				onSourceChange={(value) => changeFilter(setSource, value)}
				onTopicChange={(value) => changeFilter(setTopic, value)}
				onOrderChange={(value) => changeFilter(setOrder, value)}
			/>

			{visibleArticles.length === 0 && <Text variant="body">No article was found.</Text>}

			<div className="grid grid-cols-1 md:grid-cols-2 gap-4">
				{visibleArticles.map((article) => (
					<ArticleCard
						key={article.id}
						story={article}
						isSaved={true}
						onReadMore={() => setOpenedArticle(article)}
						onToggleSave={() => toggleSave(article.id)}
					/>
				))}
			</div>
			<Pagination currentPage={currentPage} pageCount={pageCount} onPageChange={setPage} />
			<ArticleModal story={openedArticle} onClose={() => setOpenedArticle(null)} />
		</Division>
	);
}