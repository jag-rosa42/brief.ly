export interface Profile {
	name: string;
	topic_ids: string[];
	created_at: string;
	updated_at: string;
}

// PUT creates the profile on the first call (both fields required),
// then only changes the fields that are sent.
export interface ProfileUpdate {
	name?: string;
	topic_ids?: string[];
}

export interface Topic {
	id: string;
}

export interface TopicsResponse {
	items: Topic[];
}
