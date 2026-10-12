import { useEffect, useState } from "react";
import { Button } from "@/shared/components/Button";
import { ArticleCard } from "@/shared/components/ArticleCard";
import { ArticleModal, type Story } from "@/shared/components/ArticleModal";
import { Dropdown } from "@/shared/components/Dropdown";
import { Input } from "@/shared/components/Input";
import { Text } from "@/shared/components/Text";

// Une Story (le type partagé avec ArticleCard et ArticleModal) avec un id en plus.
interface Article extends Story {
	id: number;
	readingTime: number; // en minutes
}

const ARTICLES_PER_PAGE = 4;

// Faux articles en attendant le backend.
const fakeArticles: Article[] = [
	{ id: 1, source: "Le Monde", category: "IA", title: "Les LLM en 2026", summary: "Un tour d'horizon des modèles de langage.", url: null, readingTime: 8 },
	{ id: 2, source: "Le Monde", category: "Climat", title: "Un été record", summary: "Les températures battent de nouveaux records.", url: null, readingTime: 5 },
	{ id: 3, source: "Wired", category: "IA", title: "Des agents partout", summary: "Les agents autonomes arrivent dans les entreprises.", url: null, readingTime: 12 },
	{ id: 4, source: "Wired", category: "Sécurité", title: "Mots de passe : la fin ?", summary: "Les passkeys remplacent peu à peu les mots de passe.", url: null, readingTime: 4 },
	{ id: 5, source: "Numerama", category: "Espace", title: "Retour sur la Lune", summary: "Le point sur les prochaines missions lunaires.", url: null, readingTime: 7 },
	{ id: 6, source: "Numerama", category: "IA", title: "L'IA dans les écoles", summary: "Comment les enseignants s'adaptent aux nouveaux outils.", url: null, readingTime: 6 },
	{ id: 7, source: "Le Monde", category: "Espace", title: "Un nouveau télescope", summary: "Des images inédites de galaxies lointaines.", url: null, readingTime: 3 },
	{ id: 8, source: "Wired", category: "Climat", title: "Le coût du cloud", summary: "L'empreinte carbone des centres de données.", url: null, readingTime: 10 },
	{ id: 9, source: "Numerama", category: "Sécurité", title: "Une faille géante", summary: "Des millions de routeurs concernés par une faille.", url: null, readingTime: 9 },
	{ id: 10, source: "Le Monde", category: "IA", title: "Réguler l'IA", summary: "L'Europe précise ses règles sur les modèles de langage.", url: null, readingTime: 11 },
	{ id: 11, source: "Wired", category: "Espace", title: "Internet par satellite", summary: "Les constellations de satellites encombrent l'orbite basse.", url: null, readingTime: 6 },
	{ id: 12, source: "Numerama", category: "Climat", title: "Des batteries sans lithium", summary: "Le sodium pourrait changer le stockage de l'énergie.", url: null, readingTime: 14 },
];

// À remplacer par le vrai appel API, par exemple :
//   const response = await fetch("/api/articles/saved");
//   return await response.json();
async function fetchSavedArticles(): Promise<Article[]> {
	return Promise.resolve(fakeArticles);
}

// Renvoie les valeurs sans doublon, précédées de l'option "tout afficher".
function buildOptions(values: string[], allLabel: string) {
	const uniqueValues = [...new Set(values)];
	return [
		{ value: "all", label: allLabel },
		...uniqueValues.map((value) => ({ value, label: value })),
	];
}

export function SavedArticles() {
	const [articles, setArticles] = useState<Article[]>([]);
	const [search, setSearch] = useState("");
	const [source, setSource] = useState("all");
	const [topic, setTopic] = useState("all");
	const [order, setOrder] = useState("asc");
	const [page, setPage] = useState(1);
	const [openedArticle, setOpenedArticle] = useState<Article | null>(null);

	// Appel API, une seule fois à l'arrivée sur la page.
	useEffect(() => {
		fetchSavedArticles()
			.then(setArticles)
			.catch(() => setArticles([]));
	}, []);

	// 1. Filtres
	const keywords = search.toLowerCase().split(" ").filter((word) => word !== "");
	const filteredArticles = articles.filter((article) => {
		const content = `${article.title} ${article.summary}`.toLowerCase();
		const matchesSearch = keywords.every((word) => content.includes(word));
		const matchesSource = source === "all" || article.source === source;
		const matchesTopic = topic === "all" || article.category === topic;
		return matchesSearch && matchesSource && matchesTopic;
	});

	// 2. Tri (toSorted renvoie une copie, sans modifier le tableau d'origine)
	const sortedArticles = filteredArticles.toSorted((a, b) =>
		order === "asc" ? a.readingTime - b.readingTime : b.readingTime - a.readingTime
	);

	// 3. Pagination
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

	// Sur cette page tous les articles sont sauvegardés : le bouton "Saved" retire l'article.
	// À compléter avec l'appel API qui le retire aussi côté backend.
	function removeArticle(id: number) {
		setArticles(articles.filter((article) => article.id !== id));
	}

	return (
		<div className="flex flex-col gap-6 p-6 max-w-4xl mx-auto">
			<Text variant="title">Saved Articles</Text>

			<div className="flex flex-wrap items-end gap-4">
				<Input
					name="search"
					label="Search"
					variant="sub"
					placeholder="Keywords..."
					value={search}
					onChange={(e) => changeFilter(setSearch, e.target.value)}
				/>
				<Dropdown
					name="source"
					label="Source"
					variant="main"
					options={buildOptions(articles.map((article) => article.source), "All sources")}
					value={source}
					onChange={(e) => changeFilter(setSource, e.target.value)}
				/>
				<Dropdown
					name="topic"
					label="Topic"
					variant="main"
					options={buildOptions(articles.map((article) => article.category), "All topics")}
					value={topic}
					onChange={(e) => changeFilter(setTopic, e.target.value)}
				/>
				<Dropdown
					name="order"
					label="Reading time"
					variant="main"
					options={[
						{ value: "asc", label: "Shortest first" },
						{ value: "desc", label: "Longest first" },
					]}
					value={order}
					onChange={(e) => changeFilter(setOrder, e.target.value)}
				/>
			</div>

			{visibleArticles.length === 0 && <Text variant="body">Aucun article trouvé.</Text>}

			<div className="grid grid-cols-1 md:grid-cols-2 gap-4">
				{visibleArticles.map((article) => (
					<ArticleCard
						key={article.id}
						story={article}
						isSaved={true}
						onReadMore={() => setOpenedArticle(article)}
						onToggleSave={() => removeArticle(article.id)}
					/>
				))}
			</div>

			<div className="flex items-center justify-center gap-4">
				<Button variant="primary" disabled={currentPage === 1} onClick={() => setPage(currentPage - 1)}>
					Précédent
				</Button>
				<Text variant="body">Page {currentPage} / {pageCount}</Text>
				<Button variant="primary" disabled={currentPage === pageCount} onClick={() => setPage(currentPage + 1)}>
					Suivant
				</Button>
			</div>

			<ArticleModal story={openedArticle} onClose={() => setOpenedArticle(null)} />
		</div>
	);
}
