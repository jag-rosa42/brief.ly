import { useEffect, useId, useRef } from "react";
import { Button } from "@/shared/components/Button";
import { Text } from "@/shared/components/Text";
import { Division } from "@/shared/components/Division";
import { Link } from "@/shared/components/Link";
import type { Appearance } from "@/shared/components/neomorphicVariants";

export interface Article {
	id: string;
	title: string;
	category: string;
	source: string;
	url: string | null;
	summary: string;
	readingTime?: number;
}

interface ArticleModalProps {
	article: Article | null;
	appearance?: Appearance;
	onClose: () => void;
}

export function ArticleModal({ article, appearance = "classic", onClose }: ArticleModalProps) {
	const dialogRef = useRef<HTMLDialogElement>(null);
	const titleId = useId();

	useEffect(() => {
		const dialog = dialogRef.current;
		if (!dialog) return;
		if (article && !dialog.open) {
			dialog.showModal();
		} else if (!article && dialog.open) {
			dialog.close();
		}
	}, [article]);
	useEffect(() => {
		if (!article) return;

		const previousOverflow = document.body.style.overflow;
		document.body.style.overflow = "hidden";

		return () => {
			document.body.style.overflow = previousOverflow;
		};
	}, [article]);

	function handleClick(e: React.MouseEvent<HTMLDialogElement>) {
		if (e.target === e.currentTarget) {
			onClose();
		}
	}
	const surfaceProps =
		appearance === "neomorphic"
			? ({ appearance, relief: "none" } as const)
			: ({ appearance, shadow: "none" } as const);
	return (
		<dialog
			ref={dialogRef}
			aria-labelledby={titleId}
			onClose={onClose}
			onClick={handleClick}
			className={`m-auto w-[calc(100%-2rem)] max-w-4xl max-h-[90vh] overflow-hidden rounded-xl p-0 backdrop:bg-black/50 ${appearance === "neomorphic" ? "bg-background" : "bg-white"}`}
		>
			{article && (
				<Division
					variant="featurecard"
					{...surfaceProps}
					className="relative flex max-h-[90vh] flex-col"
				>
					<Button
						type="button"
						variant="secondary"
						relief={appearance === "neomorphic" ? "up" : "none"}
						className={`absolute right-4 top-4 text-2xl ${appearance === "neomorphic" ? "flex aspect-square items-center justify-center" : "text-accent hover:text-primary"}`}
						onClick={onClose}
						aria-label="Close"
					>
						×
					</Button>
					<div className="min-h-0 flex-1 overflow-y-auto pr-2">
						<Text variant="title" id={titleId} className="pr-10">
							{article.title}
						</Text>
						{article.url && (
							<Link
								to={article.url}
								variant="primary"
								external
								className={`mt-6 mb-6 inline-flex items-center gap-2 font-semibold ${appearance === "neomorphic" ? "bg-background shadow-relief-up" : ""}`}
							>
								Read the full article on {article.source} ↗
							</Link>
						)}
						<Text variant="lead">{article.summary}</Text>
					</div>
				</Division>
			)}
		</dialog>
	);
}
