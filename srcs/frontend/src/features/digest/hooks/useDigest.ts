import { useCallback, useEffect, useRef, useState } from "react";
import { ApiError } from "@/shared/components/api/client";
import { DigestStreamError, streamAnswer, streamDigest } from "@/features/digest/api";
import type { ChatMessage, DigestOptions, DigestStatus } from "@/features/digest/types";

// What the user reads for each error (the codes: docs/api/05_ai-processing.md).
export function digestErrorMessage(err: unknown, receivedText: boolean): string {
	if (err instanceof DOMException && err.name === "TimeoutError") {
		return "The AI took too long to answer. Please try again.";
	}
	if (err instanceof DigestStreamError && receivedText) {
		return "The AI stopped in the middle of its answer. What it wrote so far is kept above.";
	}
	if (err instanceof DigestStreamError || (err instanceof ApiError && err.status >= 500)) {
		return "The AI is unavailable right now. Your brief still works; please try again later.";
	}
	if (err instanceof ApiError && err.status === 429) {
		const wait = err.retryAfterSeconds;
		return wait === null
			? "You've asked the AI a lot in a short time. Please wait a minute."
			: `You've asked the AI a lot in a short time. Try again in ${wait} s.`;
	}
	if (err instanceof ApiError && err.status === 401) {
		return "Your session has expired. Please log in again.";
	}
	if (err instanceof ApiError && err.status === 422) {
		return "The AI could not read this request. Please check what you typed.";
	}
	return "Something went wrong while writing. Please try again.";
}

// The digest and its follow-up chat: the messages on screen, and the
// request being streamed. Only one at a time: starting a new one stops the
// previous one.
export function useDigest() {
	const [messages, setMessages] = useState<ChatMessage[]>([]);
	const [status, setStatus] = useState<DigestStatus>("idle");
	const [error, setError] = useState<string | null>(null);
	const controller = useRef<AbortController | null>(null);
	const nextId = useRef(0);

	// Leaving the page stops the stream; the server then stops the AI.
	useEffect(() => () => controller.current?.abort(), []);

	// Streams one answer into a new assistant message, shown after `shown`.
	// Resolves to false when it failed or was stopped before any text: the
	// screen then goes back to `before`, and the caller can give the user
	// their text back.
	const run = useCallback(
		async (
			start: (signal: AbortSignal) => AsyncGenerator<string>,
			before: ChatMessage[],
			shown: ChatMessage[],
		): Promise<boolean> => {
			controller.current?.abort();
			const abort = new AbortController();
			controller.current = abort;
			// A newer request replaced this one: it owns the screen now.
			const isCurrent = () => controller.current === abort;
			const id = nextId.current++;
			let received = false;

			const update = (change: (message: ChatMessage) => ChatMessage) =>
				setMessages((current) => current.map((m) => (m.id === id ? change(m) : m)));

			setError(null);
			setStatus("streaming");
			setMessages([...shown, { id, role: "assistant", text: "" }]);

			try {
				for await (const chunk of start(abort.signal)) {
					if (!isCurrent()) return received;
					received = true;
					update((m) => ({ ...m, text: m.text + chunk }));
				}
				if (isCurrent()) setStatus("done");
				return true;
			} catch (err) {
				if (!isCurrent()) return received;
				if (abort.signal.aborted) {
					// The user pressed Stop.
					if (received) update((m) => ({ ...m, stopped: true }));
					else setMessages(before);
					setStatus(before.length > 0 || received ? "done" : "idle");
					return received;
				}
				setError(digestErrorMessage(err, received));
				setStatus("error");
				if (!received) setMessages(before);
				return received;
			}
		},
		[],
	);

	const generate = useCallback(
		(options: DigestOptions) => run((signal) => streamDigest(options, signal), messages, []),
		[run, messages],
	);

	const ask = useCallback(
		(question: string) => {
			const userMessage: ChatMessage = { id: nextId.current++, role: "user", text: question };
			const conversation = [...messages, userMessage];
			return run((signal) => streamAnswer(conversation, signal), messages, conversation);
		},
		[run, messages],
	);

	const stop = useCallback(() => controller.current?.abort(), []);

	return { messages, status, error, generate, ask, stop };
}

// What useDigest returns: DigestDrawer holds it, DigestPanel shows it.
export type DigestState = ReturnType<typeof useDigest>;
