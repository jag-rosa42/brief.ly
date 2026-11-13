import { FOCUS_MAX_LENGTH, QUESTION_MAX_LENGTH } from "@/features/digest/types";

// What the user types goes into the AI's prompt. "<" and ">" could close a
// block of that prompt early (prompt injection), and control characters
// (newlines included) have no place in one line of text: the backend refuses
// both with a 422, so they are refused here first, with a clear message.
const FORBIDDEN = /[<>\u0000-\u001f\u007f]/;

function checkText(text: string, maxLength: number): string | null {
	if (text.length > maxLength) {
		return `At most ${maxLength} characters.`;
	}
	if (FORBIDDEN.test(text)) {
		return "Please write one line of text, without < or >.";
	}
	return null;
}

// The focus is optional: "" is valid.
export function validateFocus(focus: string): string | null {
	return checkText(focus.trim(), FOCUS_MAX_LENGTH);
}

export function validateQuestion(question: string): string | null {
	const trimmed = question.trim();
	if (trimmed === "") {
		return "Please type a question.";
	}
	return checkText(trimmed, QUESTION_MAX_LENGTH);
}
