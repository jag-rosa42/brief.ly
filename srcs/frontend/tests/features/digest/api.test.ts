import { afterEach, describe, expect, test, vi } from "vitest";
import {
	DigestStreamError,
	streamAnswer,
	streamDigest,
	toChatRequest,
} from "@/features/digest/api";
import type { ChatMessage } from "@/features/digest/types";
import { apiStream } from "@/shared/components/api/client";

vi.mock("@/shared/components/api/client", async (importOriginal) => ({
	...(await importOriginal<typeof import("@/shared/components/api/client")>()),
	apiStream: vi.fn(),
}));

afterEach(() => {
	vi.mocked(apiStream).mockReset();
});

function sse(...events: [string, unknown][]): Response {
	const text = events.map(([event, data]) => `event: ${event}\ndata: ${JSON.stringify(data)}\n\n`);
	return new Response(text.join(""), { headers: { "Content-Type": "text/event-stream" } });
}

async function collect(stream: AsyncGenerator<string>): Promise<string[]> {
	const chunks: string[] = [];
	for await (const chunk of stream) chunks.push(chunk);
	return chunks;
}

const signal = new AbortController().signal;

describe("streamDigest", () => {
	test("posts the options and yields the text of each chunk", async () => {
		vi.mocked(apiStream).mockResolvedValue(
			sse(["chunk", { text: "Here" }], ["chunk", { text: " is" }], ["done", {}]),
		);

		const chunks = await collect(streamDigest({ length: "detailed", focus: "  finance " }, signal));

		expect(chunks).toEqual(["Here", " is"]);
		expect(apiStream).toHaveBeenCalledWith("/api/ai-processing/digest", {
			method: "POST",
			body: { length: "detailed", focus: "finance" },
			signal,
			timeoutMs: 180_000,
		});
	});

	test("throws a DigestStreamError on an error event, after the text so far", async () => {
		vi.mocked(apiStream).mockResolvedValue(
			sse(
				["chunk", { text: "Here" }],
				["error", { error: { code: "SERVICE_UNAVAILABLE", message: "Down" } }],
			),
		);
		const chunks: string[] = [];

		const reading = (async () => {
			for await (const chunk of streamDigest({ length: "short", focus: "" }, signal)) {
				chunks.push(chunk);
			}
		})();

		await expect(reading).rejects.toMatchObject({
			name: "DigestStreamError",
			code: "SERVICE_UNAVAILABLE",
		});
		expect(chunks).toEqual(["Here"]);
	});

	test("throws when the stream ends without done", async () => {
		vi.mocked(apiStream).mockResolvedValue(sse(["chunk", { text: "Here" }]));

		await expect(
			collect(streamDigest({ length: "short", focus: "" }, signal)),
		).rejects.toBeInstanceOf(DigestStreamError);
	});
});

function message(id: number, role: "user" | "assistant", text: string): ChatMessage {
	return { id, role, text };
}

describe("streamAnswer", () => {
	test("posts the conversation without the ids", async () => {
		vi.mocked(apiStream).mockResolvedValue(sse(["done", {}]));

		await collect(
			streamAnswer([message(0, "assistant", "Digest."), message(1, "user", "Why?")], signal),
		);

		expect(apiStream).toHaveBeenCalledWith(
			"/api/ai-processing/digest/chat",
			expect.objectContaining({
				body: {
					messages: [
						{ role: "assistant", content: "Digest." },
						{ role: "user", content: "Why?" },
					],
				},
			}),
		);
	});
});

describe("toChatRequest", () => {
	test("keeps the digest and the latest turns, at most 10 messages", () => {
		const conversation = [message(0, "assistant", "Digest.")];
		for (let turn = 1; turn <= 6; turn++) {
			conversation.push(message(turn * 2 - 1, "user", `Q${turn}`));
			if (turn < 6) conversation.push(message(turn * 2, "assistant", `A${turn}`));
		}

		const request = toChatRequest(conversation);

		expect(request).toHaveLength(10);
		expect(request[0]).toEqual({ role: "assistant", content: "Digest." });
		expect(request[1]).toEqual({ role: "user", content: "Q2" });
		expect(request.at(-1)).toEqual({ role: "user", content: "Q6" });
	});

	test("cleans earlier answers of characters the API refuses", () => {
		const request = toChatRequest([
			message(0, "assistant", "Line\u0007one\n\nTwo\t"),
			message(1, "user", " Why? "),
		]);

		expect(request).toEqual([
			{ role: "assistant", content: "Line one\n\nTwo" },
			{ role: "user", content: "Why?" },
		]);
	});
});
