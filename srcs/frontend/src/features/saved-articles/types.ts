export interface SavedArticle {
	article_id: string;
	title: string;
	url: string;
	summary: string | null;
	source: string;
	topic_id: string;
	read_time_minutes: number;
	saved_at: string;
}

export interface SavedArticlesResponse {
	items: SavedArticle[];
}
