// Reads a Server-Sent Events body (text/event-stream), as the digest routes
// send it (srcs/services/ai-processing/src/api/streaming.py):
//
//   event: chunk
//   data: {"text": "Here is"}
//
//   event: done
//   data: {}
//
// The browser's EventSource can't be used: it only sends GET requests and
// can't add the Authorization header. So the body of a fetch() is read here.

export interface ServerSentEvent {
	event: string;
	data: unknown;
}

function parseBlock(block: string): ServerSentEvent | null {
	let event = "message";
	const data: string[] = [];

	for (const line of block.split("\n")) {
		if (line.startsWith("event:")) {
			event = line.slice("event:".length).trim();
		} else if (line.startsWith("data:")) {
			data.push(line.slice("data:".length).trim());
		}
	}
	if (data.length === 0) {
		return null; // a comment or keep-alive: nothing to read
	}
	return { event, data: JSON.parse(data.join("\n")) as unknown };
}

// Yields each event as soon as it is complete. The network cuts the body
// anywhere, even inside a character: TextDecoder's stream mode keeps the
// incomplete bytes, and `buffer` keeps the incomplete event, until the next
// piece arrives.
export async function* readEvents(
	body: ReadableStream<Uint8Array>,
): AsyncGenerator<ServerSentEvent> {
	const reader = body.getReader();
	const decoder = new TextDecoder();
	let buffer = "";

	try {
		for (;;) {
			const { done, value } = await reader.read();
			if (done) break;
			buffer += decoder.decode(value, { stream: true }).replace(/\r\n/g, "\n");

			let end = buffer.indexOf("\n\n");
			while (end !== -1) {
				const parsed = parseBlock(buffer.slice(0, end));
				buffer = buffer.slice(end + 2);
				if (parsed !== null) yield parsed;
				end = buffer.indexOf("\n\n");
			}
		}
	} finally {
		// Stop or leave: cancel the body, which closes the connection, so the
		// server stops the AI too.
		await reader.cancel().catch(() => undefined);
	}
}
