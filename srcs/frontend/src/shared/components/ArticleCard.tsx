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
			className={`relative flex min-h-80 w-full cursor-pointer gap-5 p-7 transition hover:-translate-y-0.5 hover:shadow-[12px_16px_24px_#c5b6a599,-7px_-7px_18px_#fff9f099] ${className ?? ""}`}
		>
			<div className="flex items-center justify-between gap-2">
				<Text variant="label" className="text-primary">
					{article.source}
				</Text>
				<Text variant="body" className="font-normal normal-case text-[#7b6b62]">
					{readingTime} min read
				</Text>
			</div>
			<Text
				variant="subheading"
				className="font-serif! text-[clamp(1.35rem,1.7vw,1.85rem)]! font-semibold leading-tight tracking-tight text-accent!"
			>
				{article.title}
			</Text>

			<Text variant="body" className="line-clamp-3 text-[#7b6b62]">
				{article.summary}
			</Text>
			<div className="mt-auto flex items-center gap-2 border-t border-[#c5b6a56b] pt-4">
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
					className="group ml-auto font-sans! font-semibold after:absolute after:inset-0 after:content-['']"
				>
					Read More →
				</Button>
			</div>
		</Division>
	);
}
