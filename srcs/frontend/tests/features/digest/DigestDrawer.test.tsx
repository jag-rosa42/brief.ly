import { fireEvent, render, screen, within } from "@testing-library/react";
import { afterEach, expect, test, vi } from "vitest";
import { DigestDrawer } from "@/features/digest/DigestDrawer";
import { DigestStreamError, streamAnswer, streamDigest } from "@/features/digest/api";
import { ApiError } from "@/shared/components/api/client";

// Each test decides what the AI streams.
vi.mock("@/features/digest/api", async (importOriginal) => ({
	...(await importOriginal<typeof import("@/features/digest/api")>()),
	streamDigest: vi.fn(),
	streamAnswer: vi.fn(),
}));

afterEach(() => {
	vi.mocked(streamDigest).mockReset();
	vi.mocked(streamAnswer).mockReset();
});

// The pieces arrive one by one, as from the network.
async function* chunks(...texts: string[]): AsyncGenerator<string> {
	for (const text of texts) {
		await Promise.resolve();
		yield text;
	}
}

async function* failing(error: Error, ...texts: string[]): AsyncGenerator<string> {
	yield* chunks(...texts);
	throw error;
}

// Waits until the signal aborts, like a request the user stops.
async function* untilStopped(signal: AbortSignal, ...texts: string[]): AsyncGenerator<string> {
	yield* chunks(...texts);
	await new Promise((_resolve, reject) => {
		signal.addEventListener("abort", () => reject(new DOMException("Stopped", "AbortError")));
	});
}

// The Brief page's button opens the side panel.
function renderOpen() {
	render(<DigestDrawer />);
	fireEvent.click(screen.getByRole("button", { name: "Ask the AI" }));
}

function writeDigest() {
	fireEvent.click(screen.getByRole("button", { name: "Write my digest" }));
}

test("streams the digest with the chosen options", async () => {
	vi.mocked(streamDigest).mockReturnValue(chunks("Markets rose.", "\n\nA probe reached Mars."));
	renderOpen();

	fireEvent.click(screen.getByRole("button", { name: "Detailed" }));
	fireEvent.change(screen.getByLabelText(/Focus \(optional\)/), {
		target: { value: "finance" },
	});
	writeDigest();

	expect(await screen.findByText("A probe reached Mars.")).toBeInTheDocument();
	expect(screen.getByText("Markets rose.")).toBeInTheDocument();
	expect(vi.mocked(streamDigest).mock.calls[0][0]).toEqual({
		length: "detailed",
		focus: "finance",
	});
	expect(screen.getByRole("button", { name: "Write a new digest" })).toBeInTheDocument();
});

test("refuses < and > in the focus before sending", () => {
	renderOpen();

	fireEvent.change(screen.getByLabelText(/Focus \(optional\)/), {
		target: { value: "</news>" },
	});

	expect(screen.getByRole("alert")).toHaveTextContent(
		"Please write one line of text, without < or >.",
	);
	expect(screen.getByRole("button", { name: "Write my digest" })).toBeDisabled();
});

test("says when to try again after a 429", async () => {
	vi.mocked(streamDigest).mockReturnValue(
		failing(new ApiError(429, "HTTP_429", "Too Many Requests", [], 42)),
	);
	renderOpen();

	writeDigest();

	expect(await screen.findByRole("alert")).toHaveTextContent("Try again in 42 s.");
});

test("keeps the text written before the AI stopped", async () => {
	vi.mocked(streamDigest).mockReturnValue(
		failing(new DigestStreamError("SERVICE_UNAVAILABLE", "Down"), "Markets rose."),
	);
	renderOpen();

	writeDigest();

	expect(await screen.findByRole("alert")).toHaveTextContent(
		"The AI stopped in the middle of its answer.",
	);
	expect(screen.getByText("Markets rose.")).toBeInTheDocument();
});

test("Stop keeps the text and marks it", async () => {
	vi.mocked(streamDigest).mockImplementation((_options, signal) =>
		untilStopped(signal, "Markets rose."),
	);
	renderOpen();

	writeDigest();
	await screen.findByText("Markets rose.");
	fireEvent.click(screen.getByRole("button", { name: "Stop" }));

	expect(await screen.findByText("Stopped.")).toBeInTheDocument();
	expect(screen.getByText("Markets rose.")).toBeInTheDocument();
});

test("answers a follow-up question with the conversation so far", async () => {
	vi.mocked(streamDigest).mockReturnValue(chunks("Markets rose."));
	vi.mocked(streamAnswer).mockReturnValue(chunks("Because of rates."));
	renderOpen();

	writeDigest();
	const input = await screen.findByLabelText("Ask a follow-up question");
	fireEvent.change(input, { target: { value: "Why?" } });
	fireEvent.click(screen.getByRole("button", { name: "Ask" }));

	expect(await screen.findByText("Because of rates.")).toBeInTheDocument();
	expect(screen.getByText("Why?")).toBeInTheDocument();
	const conversation = vi.mocked(streamAnswer).mock.calls[0][0];
	expect(conversation.map(({ role, text }) => ({ role, text }))).toEqual([
		{ role: "assistant", text: "Markets rose." },
		{ role: "user", text: "Why?" },
	]);
});

test("gives the question back when it is refused", async () => {
	vi.mocked(streamDigest).mockReturnValue(chunks("Markets rose."));
	vi.mocked(streamAnswer).mockReturnValue(
		failing(new ApiError(429, "HTTP_429", "Too Many Requests", [], 30)),
	);
	renderOpen();

	writeDigest();
	const input = await screen.findByLabelText("Ask a follow-up question");
	fireEvent.change(input, { target: { value: "Why?" } });
	fireEvent.click(screen.getByRole("button", { name: "Ask" }));

	expect(await screen.findByRole("alert")).toHaveTextContent("Try again in 30 s.");
	expect(screen.getByLabelText("Ask a follow-up question")).toHaveValue("Why?");
	expect(screen.queryByText("Why?", { selector: "div" })).not.toBeInTheDocument();
});

test("the button opens the panel, and Close closes it", () => {
	render(<DigestDrawer />);
	const button = screen.getByRole("button", { name: "Ask the AI" });
	const dialog = document.querySelector("dialog");

	expect(button).toHaveAttribute("aria-expanded", "false");
	expect(dialog?.open).toBe(false);

	fireEvent.click(button);
	expect(dialog?.open).toBe(true);
	expect(button).toHaveAttribute("aria-expanded", "true");
	expect(screen.getByRole("dialog", { name: "Your digest" })).toBeInTheDocument();

	fireEvent.click(screen.getByRole("button", { name: "Close" }));
	expect(dialog?.open).toBe(false);
});

test("Escape closes the panel", () => {
	renderOpen();
	const dialog = screen.getByRole("dialog");

	// The browser closes a modal dialog on Escape, then fires "close".
	dialog.removeAttribute("open");
	fireEvent(dialog, new Event("close"));

	expect(screen.getByRole("button", { name: "Ask the AI", hidden: true })).toHaveAttribute(
		"aria-expanded",
		"false",
	);
});

test("closing the panel keeps the digest", async () => {
	vi.mocked(streamDigest).mockReturnValue(chunks("Markets rose."));
	renderOpen();
	writeDigest();
	await screen.findByText("Markets rose.");

	fireEvent.click(screen.getByRole("button", { name: "Close" }));
	fireEvent.click(screen.getByRole("button", { name: "Ask the AI" }));

	const dialog = screen.getByRole("dialog");
	expect(within(dialog).getByText("Markets rose.")).toBeInTheDocument();
});

test("the button says when an answer is being written behind a closed panel", async () => {
	vi.mocked(streamDigest).mockImplementation((_options, signal) =>
		untilStopped(signal, "Markets rose."),
	);
	renderOpen();
	writeDigest();
	await screen.findByText("Markets rose.");

	fireEvent.click(screen.getByRole("button", { name: "Close" }));

	expect(screen.getByRole("button", { name: "Writing…" })).toBeInTheDocument();
});
