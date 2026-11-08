import { Division } from "@/shared/components/Division";
import { Text } from "@/shared/components/Text";
import { Button } from "@/shared/components/Button";
import type { Article } from "@/shared/components/ArticleModal";

const MOCK_READING_TIME = 4;

interface ArticleCardProps {
	article: Article;
	isSaved: boolean;
	onReadMore: () => void;
	onToggleSave: () => void;
	className?: string;
}

export function ArticleCard({
	article,
	isSaved,
	onReadMore,
	onToggleSave,
	className,
}: ArticleCardProps) {
	const readingTime = article.readingTime ?? MOCK_READING_TIME;
	return (
		<Division
			variant="dashboardcard"
			className={`relative flex w-full cursor-pointer shadow-sm transition hover:-translate-y-0.5 hover:shadow-soft-hover ${className ?? ""}`}
		>
			<div className="flex items-center justify-between gap-2">
				<Text variant="label" className="text-accent">
					{article.source}
				</Text>
				<Text variant="body" className="font-normal normal-case text-info">
					{readingTime} min read
				</Text>
			</div>
			<Text variant="subheading">{article.title}</Text>

			<Text variant="body" className="line-clamp-3 text-accent/80">
				{article.summary}
			</Text>
			<div className="mt-auto flex items-center gap-2 border-t border-secondary/30 pt-4">
				<Button
					type="button"
					variant={isSaved ? "secondary" : "primary"}
					onClick={onToggleSave}
					aria-pressed={isSaved}
					// Same border and width in both states: the button keeps its shape.
					className="relative z-10 min-w-24 border-1 border-primary hover:border-primary-dark"
				>
					{isSaved ? "Saved" : "Save"}
				</Button>
				<Button
					type="button"
					variant="simple"
					onClick={onReadMore}
					className="group ml-auto font-semibold after:absolute after:inset-0 after:content-['']"
				>
					Read More →
				</Button>
			</div>
		</Division>
	);
}
