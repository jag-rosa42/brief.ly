export interface BriefingProfile {
	name: string;
	topic_ids: string[];
	saved_article_ids: string[];
}

export interface BriefingArticle {
	article_id: string;
	title: string;
	publisher_name: string;
	url: string;
	summary: string | null;
	read_time_minutes: number;
	topic_id: string;
}

export interface TopicCluster {
	topic_id: string;
	summary: string | null;
	articles: BriefingArticle[];
}

export interface Briefing {
	profile: BriefingProfile;
	topic_clusters: TopicCluster[];
}
