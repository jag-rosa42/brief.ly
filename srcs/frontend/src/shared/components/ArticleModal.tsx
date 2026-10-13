import { useEffect, useId, useRef } from "react";
import { Button } from "@/shared/components/Button";
import { Text } from "@/shared/components/Text";
import { Division } from "@/shared/components/Division";
import { Link } from "@/shared/components/Link";

export interface Story {
	id: string;
	title: string;
	category: string;
	source: string;
	url: string | null;
	summary: string;
	readingTime?: number;
}

interface ArticleModalProps {
	story: Story | null;
	onClose: () => void;
}

export function ArticleModal({ story, onClose }: ArticleModalProps) {
	const dialogRef = useRef<HTMLDialogElement>(null);
	const titleId = useId();

	useEffect(() => {
		const dialog = dialogRef.current;
		if(!dialog)
			return;
		if (story && !dialog.open) {
			dialog.showModal();
		} else if (!story && dialog.open) {
			dialog.close();
		}
	}, [story]);
	useEffect(() => {
	if (!story) return;

	const previousOverflow = document.body.style.overflow;
	document.body.style.overflow = "hidden";

	return () => {
		document.body.style.overflow = previousOverflow;
	};
}, [story]);

	function handleClick(e: React.MouseEvent<HTMLDialogElement>) {
		if (e.target === e.currentTarget) {
			onClose();
		}
	}
	return (
		<dialog
			ref={dialogRef}
			aria-labelledby={titleId}
			onClose={onClose}
			onClick={handleClick}
			className="m-auto w-[calc(100%-2rem)] max-w-4xl max-h-[90vh] bg-transparent p-0 backdrop:bg-black/50"
		>
			{story && (
				<Division
					variant="featurecard"
					className="relative flex max-h-[90vh] flex-col shadow-sm"
				>
					<Button
						type="button"
						variant="secondary"
						className="absolute right-4 top-4 text-2xl text-accent hover:text-primary"
						onClick={onClose}
						aria-label="Close"
					>
						x
					</Button>
					<div className="min-h-0 flex-1 overflow-y-auto pr-2">
						<Text variant="title" id={titleId} className="pr-10">
							{story.title}
						</Text>
							{story.url && (
							<Link
								to={story.url}
								variant="primary"
								external
								className="mt-6 mb-6 inline-flex items-center gap-2 font-semibold"
							>
								Read the full article on {story.source} ↗
							</Link>
						)}
						<Text variant="lead">
							{story.summary}
						</Text>
					</div>
				</Division>
			)}
		</dialog>
	);
}