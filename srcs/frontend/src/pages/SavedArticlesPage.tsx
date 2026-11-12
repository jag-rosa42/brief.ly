import { useState } from "react";
import { Button } from "@/shared/components/Button";
import { ArticleCard } from "@/shared/components/ArticleCard";
import { ArticleModal, type Article } from "@/shared/components/ArticleModal";
import { Dropdown } from "@/shared/components/Dropdown";
import { Icon } from "@/shared/components/Icon";
import { Input } from "@/shared/components/Input";
import { Text } from "@/shared/components/Text";
import { Division } from "@/shared/components/Division";
import { toArticle } from "@/shared/utils/article";
import { Spinner } from "@/shared/components/Spinner";
import { useSavedArticlesList } from "@/features/saved-articles/hooks/useSavedArticlesList";

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

interface FilterValues {
	search: string;
	source: string;
	topic: string;
}

function filterArticles(articles: Article[], { search, source, topic }: FilterValues): Article[] {
	const keywords = search
		.toLowerCase()
		.split(" ")
		.filter((word) => word !== "");

	return articles.filter((article) => {
		const content = `${article.title} ${article.summary}`.toLowerCase();
		const matchesSearch = keywords.every((word) => content.includes(word));
		const matchesSource = source === "all" || article.source === source;
		const matchesTopic = topic === "all" || article.category === topic;
		return matchesSearch && matchesSource && matchesTopic;
	});
}

function sortByReadingTime(articles: Article[], order: string): Article[] {
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
	articles: Article[];
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
		// One filter per line on a phone, two per row from sm, one row from md.
		<div className="grid grid-cols-1 gap-4 sm:grid-cols-2 md:flex md:flex-wrap md:items-end">
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
				options={buildOptions(
					articles.map((article) => article.source),
					"All sources",
				)}
				value={source}
				onChange={(e) => onSourceChange(e.target.value)}
			/>
			<Dropdown
				name="topic"
				label="Topic"
				variant="main"
				options={buildOptions(
					articles.map((article) => article.category),
					"All topics",
				)}
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
			<Button
				variant="primary"
				aria-label="Previous page"
				disabled={currentPage === 1}
				onClick={() => onPageChange(currentPage - 1)}
			>
				<Icon name="arrow-left" />
			</Button>
			<Text variant="body">
				Page {currentPage} / {pageCount}
			</Text>
			<Button
				variant="primary"
				aria-label="Next page"
				disabled={currentPage === pageCount}
				onClick={() => onPageChange(currentPage + 1)}
			>
				<Icon name="arrow-right" />
			</Button>
		</div>
	);
}

export function SavedArticles() {
	const { data, isLoading, error, remove } = useSavedArticlesList();

	const [search, setSearch] = useState("");
	const [source, setSource] = useState("all");
	const [topic, setTopic] = useState("all");
	const [order, setOrder] = useState("asc");
	const [page, setPage] = useState(1);
	const [openedArticle, setOpenedArticle] = useState<Article | null>(null);

	if (isLoading) {
		return <Spinner />;
	}

	if (error) {
		return (
			<Division variant="dashboardpage" className="max-w-4xl gap-6">
				<Text variant="title">Saved Articles</Text>
				<Text variant="body">Your saved articles couldn't be loaded. Please try again later.</Text>
			</Division>
		);
	}

	const articles = data.map(toArticle);

	if (articles.length === 0) {
		return (
			<Division variant="dashboardpage" className="max-w-4xl gap-6">
				<Text variant="title">Saved Articles</Text>
				<Text variant="body">You haven't saved any article yet.</Text>
			</Division>
		);
	}

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

			{visibleArticles.length === 0 && <Text variant="body">No article matches the filters.</Text>}

			<div className="grid grid-cols-1 md:grid-cols-2 gap-4">
				{visibleArticles.map((article) => (
					<ArticleCard
						key={article.id}
						article={article}
						isSaved={true}
						onReadMore={() => setOpenedArticle(article)}
						onToggleSave={() => {
							void remove(article.id);
						}}
					/>
				))}
			</div>
			<Pagination currentPage={currentPage} pageCount={pageCount} onPageChange={setPage} />
			<ArticleModal article={openedArticle} onClose={() => setOpenedArticle(null)} />
		</Division>
	);
}
