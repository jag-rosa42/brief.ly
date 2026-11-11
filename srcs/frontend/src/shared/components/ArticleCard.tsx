import { Division } from "@/shared/components/Division";
import { Text } from "@/shared/components/Text";
import { Button } from "@/shared/components/Button";
import type { Article } from "@/shared/components/ArticleModal";
import type { Appearance } from "@/shared/components/neomorphicVariants";

const MOCK_READING_TIME = 4;

interface ArticleCardProps {
	article: Article;
	isSaved: boolean;
	onReadMore: () => void;
	onToggleSave: () => void;
	className?: string;
	appearance?: Appearance;
}

export function ArticleCard({
	article,
	isSaved,
	onReadMore,
	onToggleSave,
	className,
	appearance = "classic",
}: ArticleCardProps) {
	const readingTime = article.readingTime ?? MOCK_READING_TIME;
	const surfaceProps =
		appearance === "neomorphic"
			? ({ appearance, relief: "up" } as const)
			: ({ appearance, shadow: "sm-hover-soft" } as const);
	return (
		<Division
			variant="dashboardcard"
			{...surfaceProps}
			className={`relative flex h-full w-full cursor-pointer transition hover:-translate-y-0.5 ${appearance === "neomorphic" ? "hover:shadow-relief-up-hover" : ""} ${className ?? ""}`}
		>
			<div className="flex items-center justify-between gap-2">
				<Text variant="label" className="text-accent">
					{article.source}
				</Text>
				<Text variant="body" className="font-normal normal-case text-info">
					{readingTime} min read
				</Text>
			</div>
			<Text
				variant="subheading"
				className="line-clamp-4 min-h-[7rem] text-base"
				title={article.title}
			>
				{article.title}
			</Text>

			<Text variant="body" className="line-clamp-3 text-accent/80 text-sm">
				{article.summary}
			</Text>
			<div className="mt-auto flex items-center gap-2 border-t border-secondary/30 pt-4">
				<Button
					type="button"
					variant="simple"
					onClick={onReadMore}
					className={`group mr-auto font-semibold after:absolute after:inset-0 after:content-[''] ${appearance === "neomorphic" ? "rounded-full bg-background px-4 py-2" : ""}`}
				>
					Read more
				</Button>
				<Button
					type="button"
					variant={isSaved ? "secondary" : "side"}
					relief={appearance === "neomorphic" ? (isSaved ? "down" : "up") : "none"}
					onClick={onToggleSave}
					aria-pressed={isSaved}
					// Same border and width in both states: the button keeps its shape.
					className={`relative z-10 min-w-20 px-3 py-1 text-sm hover:border-primary-dark ${appearance === "neomorphic" && !isSaved ? "bg-background" : ""}`}
				>
					{isSaved ? "Saved" : "Save"}
				</Button>
			</div>
		</Division>
	);
}
