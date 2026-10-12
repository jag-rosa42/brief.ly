import { Division } from "@/shared/components/Division";
import { Text } from "@/shared/components/Text";
import { Button } from "@/shared/components/Button";
import type { Story } from "@/shared/components/ArticleModal";

const MOCK_READING_TIME = 4;

interface ArticleCardProps {
	story: Story;
	isSaved: boolean;
	onReadMore: () => void;
	onToggleSave: () => void;
	className?: string;
}

export function ArticleCard({
	story,
	isSaved,
	onReadMore,
	onToggleSave,
	className,
}: ArticleCardProps) {
	const readingTime = story.readingTime ?? MOCK_READING_TIME;
	return (
		<Division
			variant="featurecard"
			className={`relative flex w-full max-w-sm cursor-pointer shadow-sm transition-shadow hover:shadow-md ${className ?? ""}`}
		>
			<div className="flex items-center justify-between gap-2 text-xs font-semibold uppercase tracking-wide">
				<Text variant="body">{story.source}</Text>
        		<Text variant="body" className="font-normal normal-case text-gray-500">
          			{readingTime} min read
        		</Text>
			</div>
			<Text variant="subheading">
				{story.title}
			</Text>
			
			<Text variant="body" className="line-clamp-3 text-gray-600">
				{story.summary}
			</Text>
			<div className="mt-auto flex items-center gap-2 border-t border-gray-100 pt-4">
				<Button
					type="button"
					variant="secondary"
					onClick={onToggleSave}
					aria-pressed={isSaved}
					className="relative z-10"
				>
					{isSaved ? "Saved" : "Save for later"}
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