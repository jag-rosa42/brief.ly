// The digest and its follow-up chat (ADR-0011, docs/api/05_ai-processing.md).
//
// The limits repeat the backend's (srcs/services/ai-processing/src/domain/
// value_objects/digest.py): the user sees the error before sending, and the
// backend still checks everything.

export type DigestLength = "short" | "detailed";

export const FOCUS_MAX_LENGTH = 200;
export const QUESTION_MAX_LENGTH = 500;
export const ANSWER_MAX_LENGTH = 4000;
// The whole conversation sent with a question, the new question included.
export const MAX_CHAT_MESSAGES = 10;

export interface DigestOptions {
	length: DigestLength;
	// Optional free text: what the user cares about today. "" for none.
	focus: string;
}

export interface ChatMessage {
	// Only for React's list keys: never sent.
	id: number;
	role: "user" | "assistant";
	text: string;
	// The user pressed Stop: the text is kept, marked as cut.
	stopped?: boolean;
}

export type DigestStatus = "idle" | "streaming" | "done" | "error";

// One message as the API expects it (POST /digest/chat).
export interface ChatMessageRequest {
	role: "user" | "assistant";
	content: string;
}
