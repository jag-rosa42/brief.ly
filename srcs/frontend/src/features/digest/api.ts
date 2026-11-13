import { ApiError, apiStream } from "@/shared/components/api/client";
import { readEvents } from "@/features/digest/sse";
import {
	ANSWER_MAX_LENGTH,
	MAX_CHAT_MESSAGES,
	type ChatMessage,
	type ChatMessageRequest,
	type DigestOptions,
} from "@/features/digest/types";

const DIGEST_PATH = "/api/ai-processing/digest";
const CHAT_PATH = "/api/ai-processing/digest/chat";
// The AI may take a while before its first words (loading the model,
// reading the news): far longer than the usual 10 s.
const STREAM_TIMEOUT_MS = 180_000;

// The answer had started (200) and then failed: the backend sends an `error`
// event, since the status can't change any more.
export class DigestStreamError extends ApiError {
	constructor(code: string, message: string) {
		super(200, code, message);
		this.name = "DigestStreamError";
	}
}

interface ChunkData {
	text: string;
}

interface ErrorData {
	error?: { code?: string; message?: string };
}

async function* streamText(
	path: string,
	body: unknown,
	signal: AbortSignal,
): AsyncGenerator<string> {
	const response = await apiStream(path, {
		method: "POST",
		body,
		signal,
		timeoutMs: STREAM_TIMEOUT_MS,
	});
	if (response.body === null) {
		throw new DigestStreamError("EMPTY_STREAM", "The answer was empty.");
	}

	for await (const { event, data } of readEvents(response.body)) {
		if (event === "chunk") {
			yield (data as ChunkData).text;
		} else if (event === "done") {
			return;
		} else if (event === "error") {
			const { error } = data as ErrorData;
			throw new DigestStreamError(
				error?.code ?? "STREAM_ERROR",
				error?.message ?? "The answer stopped.",
			);
		}
	}
	// The connection ended without `done`: the answer was cut.
	throw new DigestStreamError("INCOMPLETE_STREAM", "The answer was cut.");
}

export function streamDigest(options: DigestOptions, signal: AbortSignal): AsyncGenerator<string> {
	return streamText(DIGEST_PATH, { length: options.length, focus: options.focus.trim() }, signal);
}

// The server keeps no conversation: it is sent with each question. Only
// what fits the API's limits: the digest first, then the most recent turns,
// and earlier answers cleaned of characters the API refuses.
export function toChatRequest(conversation: ChatMessage[]): ChatMessageRequest[] {
	const [digest, ...rest] = conversation;
	// Drop the oldest question-and-answer pairs after the digest.
	while (rest.length + 1 > MAX_CHAT_MESSAGES) {
		rest.splice(0, 2);
	}
	return [digest, ...rest].map((message) => ({
		role: message.role,
		content:
			message.role === "assistant"
				? message.text
						.replace(/[\u0000-\u0009\u000b-\u001f\u007f]/g, " ")
						.trim()
						.slice(0, ANSWER_MAX_LENGTH)
				: message.text.trim(),
	}));
}

export function streamAnswer(
	conversation: ChatMessage[],
	signal: AbortSignal,
): AsyncGenerator<string> {
	return streamText(CHAT_PATH, { messages: toChatRequest(conversation) }, signal);
}
