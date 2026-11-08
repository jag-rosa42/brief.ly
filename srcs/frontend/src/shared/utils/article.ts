import type { Article } from "@/shared/components/ArticleModal";

// Topic ids are lowercase words ("technologies"): shown with a capital letter.
export function topicLabel(topicId: string): string {
	return topicId.charAt(0).toUpperCase() + topicId.slice(1);
}

export interface ArticleResponse {
	article_id: string;
	title: string;
	url: string;
	summary: string | null;
	publisher_name: string;
	topic_id: string;
	read_time_minutes: number;
}

export function toArticle(article: ArticleResponse): Article {
	return {
		id: article.article_id,
		title: article.title,
		summary: article.summary ?? "",
		url: article.url,
		source: article.publisher_name,
		category: topicLabel(article.topic_id),
		readingTime: article.read_time_minutes,
	};
}
