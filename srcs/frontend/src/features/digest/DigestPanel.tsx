// The content of the "Your digest" side panel (ADR-0011): the AI writes one
// short read from the summaries of the user's topics, then answers
// follow-up questions about it. Both answers appear as they are written.
// DigestDrawer.tsx opens it from a button and holds its state.

import { useEffect, useRef, useState, type FormEvent } from "react";
import { Button } from "@/shared/components/Button";
import { Icon } from "@/shared/components/Icon";
import { Input } from "@/shared/components/Input";
import { Text } from "@/shared/components/Text";
import type { DigestState } from "@/features/digest/hooks/useDigest";
import { validateFocus, validateQuestion } from "@/features/digest/validation";
import {
	FOCUS_MAX_LENGTH,
	QUESTION_MAX_LENGTH,
	type ChatMessage,
	type DigestLength,
} from "@/features/digest/types";

const LENGTHS: { value: DigestLength; label: string }[] = [
	{ value: "short", label: "Short" },
	{ value: "detailed", label: "Detailed" },
];

function MessageBubble({ message, isStreaming }: { message: ChatMessage; isStreaming: boolean }) {
	if (message.role === "user") {
		return (
			<div className="ml-auto max-w-[85%] rounded-3xl rounded-br-md bg-primary px-4 py-2 break-words text-background">
				{message.text}
			</div>
		);
	}

	// Plain text, never HTML: whatever the AI writes is shown as text, so
	// an answer containing "<script>" can't run.
	const paragraphs = message.text.split("\n\n");
	return (
		<div className="flex flex-col gap-3">
			{paragraphs.map((paragraph, index) => (
				// Paragraphs only grow at the end and never move: the index is a stable key.
				// eslint-disable-next-line react-x/no-array-index-key
				<Text key={index} variant="body" className="break-words text-accent/90">
					{paragraph}
					{isStreaming && index === paragraphs.length - 1 && (
						<span
							aria-hidden="true"
							className="ml-0.5 inline-block h-4 w-2 animate-pulse bg-primary align-middle"
						/>
					)}
				</Text>
			))}
			{message.stopped && (
				<Text variant="body" className="text-sm italic text-info">
					Stopped.
				</Text>
			)}
		</div>
	);
}

interface DigestPanelProps {
	// The digest's state, held by the drawer so it survives closing it.
	digest: DigestState;
	// The id of the panel's title, which names the dialog.
	titleId: string;
	onClose: () => void;
}

export function DigestPanel({ digest, titleId, onClose }: DigestPanelProps) {
	const { messages, status, error, generate, ask, stop } = digest;
	const [length, setLength] = useState<DigestLength>("short");
	const [focus, setFocus] = useState("");
	const [question, setQuestion] = useState("");
	const scrollArea = useRef<HTMLDivElement>(null);

	const isStreaming = status === "streaming";
	const hasDigest = messages.length > 0;
	const focusError = validateFocus(focus);
	// No "type a question" error on an empty field: the button is disabled.
	const questionError = question.trim() === "" ? null : validateQuestion(question);

	// Keep the text being written in view, as a chat does.
	useEffect(() => {
		const area = scrollArea.current;
		if (area && isStreaming) area.scrollTop = area.scrollHeight;
	}, [messages, isStreaming]);

	function onGenerate(event: FormEvent) {
		event.preventDefault();
		if (focusError !== null) return;
		void generate({ length, focus });
	}

	async function onAsk(event: FormEvent) {
		event.preventDefault();
		const asked = question.trim();
		if (validateQuestion(asked) !== null) return;
		setQuestion("");
		// Refused before any answer (429, AI down...): give the question back.
		if (!(await ask(asked))) setQuestion(asked);
	}

	return (
		<div className="flex h-full flex-col bg-background shadow-soft">
			<header className="flex items-start justify-between gap-4 border-b border-accent/10 px-6 py-4">
				<div>
					<Text variant="label" className="text-info">
						Written by AI
					</Text>
					<Text variant="subheading" id={titleId}>
						Your digest
					</Text>
				</div>
				<button
					type="button"
					onClick={onClose}
					aria-label="Close"
					className="rounded-full p-2 text-accent hover:text-primary"
				>
					<Icon name="close" />
				</button>
			</header>

			<div
				ref={scrollArea}
				className="flex min-h-0 flex-1 flex-col gap-5 overflow-y-auto px-6 py-5"
			>
				<Text variant="body" className="text-info">
					One short read that ties your topics together. Choose how you want it.
				</Text>

				<form onSubmit={onGenerate} className="flex flex-col gap-4">
					<fieldset className="flex flex-col gap-1">
						<legend className="mb-1">Length</legend>
						<div className="flex gap-2">
							{LENGTHS.map((option) => (
								<Button
									key={option.value}
									type="button"
									variant="chip"
									selected={length === option.value}
									aria-pressed={length === option.value}
									disabled={isStreaming}
									onClick={() => setLength(option.value)}
								>
									{option.label}
								</Button>
							))}
						</div>
					</fieldset>

					<Input
						label="Focus (optional)"
						name="digest-focus"
						variant="sub"
						placeholder="e.g. what matters for someone working in finance"
						maxLength={FOCUS_MAX_LENGTH}
						value={focus}
						disabled={isStreaming}
						error={focusError ?? undefined}
						info={focusError ? undefined : `${focus.length}/${FOCUS_MAX_LENGTH}`}
						onChange={(e) => setFocus(e.target.value)}
					/>

					<div className="flex flex-wrap gap-3">
						{isStreaming ? (
							<Button type="button" variant="primary" onClick={stop}>
								Stop
							</Button>
						) : (
							<Button type="submit" variant="secondary" disabled={focusError !== null}>
								{hasDigest ? "Write a new digest" : "Write my digest"}
							</Button>
						)}
					</div>
				</form>

				{hasDigest && (
					<section
						aria-label="Your digest and follow-up answers"
						aria-live="polite"
						aria-busy={isStreaming}
						className="flex flex-col gap-4 rounded-3xl border border-white/70 bg-white/70 p-5"
					>
						{messages.map((message, index) => (
							<MessageBubble
								key={message.id}
								message={message}
								isStreaming={isStreaming && index === messages.length - 1}
							/>
						))}
						{isStreaming && messages.at(-1)?.text === "" && (
							<Text variant="body" className="text-sm text-info">
								Thinking…
							</Text>
						)}
					</section>
				)}

				{error && (
					<Text variant="error" role="alert">
						{error}
					</Text>
				)}

				<Text variant="body" className="text-xs text-info">
					Written from today's summaries of your topics. AI can make mistakes: check the stories
					before relying on it.
				</Text>
			</div>

			{/* The question box stays at the bottom, as in a chat. */}
			{hasDigest && (
				<form
					onSubmit={(event) => void onAsk(event)}
					className="flex items-start gap-2 border-t border-accent/10 px-6 py-4"
				>
					<div className="min-w-0 flex-1">
						<Input
							aria-label="Ask a follow-up question"
							name="digest-question"
							variant="sub"
							className="w-full"
							placeholder="Ask a follow-up, e.g. tell me more about business"
							maxLength={QUESTION_MAX_LENGTH}
							value={question}
							disabled={isStreaming}
							error={questionError ?? undefined}
							onChange={(e) => setQuestion(e.target.value)}
						/>
					</div>
					<Button
						type="submit"
						variant="primary"
						disabled={isStreaming || question.trim() === "" || questionError !== null}
					>
						Ask
					</Button>
				</form>
			)}
		</div>
	);
}
