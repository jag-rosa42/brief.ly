import { describe, expect, test } from "vitest";
import { readEvents, type ServerSentEvent } from "@/features/digest/sse";

// A body that arrives in the given pieces, cut anywhere.
function body(pieces: (string | Uint8Array)[]): ReadableStream<Uint8Array> {
	const encoder = new TextEncoder();
	return new ReadableStream({
		start(controller) {
			for (const piece of pieces) {
				controller.enqueue(typeof piece === "string" ? encoder.encode(piece) : piece);
			}
			controller.close();
		},
	});
}

async function collect(stream: ReadableStream<Uint8Array>): Promise<ServerSentEvent[]> {
	const events: ServerSentEvent[] = [];
	for await (const event of readEvents(stream)) events.push(event);
	return events;
}

describe("readEvents", () => {
	test("reads chunk events then done", async () => {
		const events = await collect(
			body([
				'event: chunk\ndata: {"text": "Here"}\n\n',
				'event: chunk\ndata: {"text": " is"}\n\nevent: done\ndata: {}\n\n',
			]),
		);

		expect(events).toEqual([
			{ event: "chunk", data: { text: "Here" } },
			{ event: "chunk", data: { text: " is" } },
			{ event: "done", data: {} },
		]);
	});

	test("waits for an event cut in the middle", async () => {
		const events = await collect(body(["event: chu", 'nk\ndata: {"te', 'xt": "Hi"}\n', "\n"]));

		expect(events).toEqual([{ event: "chunk", data: { text: "Hi" } }]);
	});

	test("keeps a character cut between two pieces", async () => {
		// "é" is two bytes in UTF-8; the network may split them.
		const bytes = new TextEncoder().encode('event: chunk\ndata: {"text": "café"}\n\n');
		const cut = bytes.indexOf(0xc3) + 1;

		const events = await collect(body([bytes.slice(0, cut), bytes.slice(cut)]));

		expect(events).toEqual([{ event: "chunk", data: { text: "café" } }]);
	});

	test("reads an error event", async () => {
		const events = await collect(
			body([
				'event: error\ndata: {"error": {"code": "SERVICE_UNAVAILABLE", "message": "Down"}}\n\n',
			]),
		);

		expect(events).toEqual([
			{ event: "error", data: { error: { code: "SERVICE_UNAVAILABLE", message: "Down" } } },
		]);
	});

	test("accepts CRLF line endings and skips comments", async () => {
		const events = await collect(body([": keep-alive\r\n\r\nevent: done\r\ndata: {}\r\n\r\n"]));

		expect(events).toEqual([{ event: "done", data: {} }]);
	});
});
