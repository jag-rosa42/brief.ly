// The AI digest on the Brief page (ADR-0011): a button in the bottom-right
// corner opens a side panel from the right. The AI stays one click away
// without taking the page's place: the news comes first.
//
// The panel is a native <dialog> opened with showModal(), which gives what a
// side panel needs for free: it sits above the page, Escape closes it, the
// keyboard focus stays inside while it's open and goes back to the button
// when it closes, and the rest of the page is hidden from screen readers.

import { useEffect, useId, useRef, useState } from "react";
import { Button } from "@/shared/components/Button";
import { Icon } from "@/shared/components/Icon";
import { DigestPanel } from "@/features/digest/DigestPanel";
import { useDigest } from "@/features/digest/hooks/useDigest";

export function DigestDrawer() {
	// Held here, not in the panel: closing the panel keeps the digest, the
	// conversation, and an answer being written. Leaving the page stops it.
	const digest = useDigest();
	const [open, setOpen] = useState(false);
	const dialogRef = useRef<HTMLDialogElement>(null);
	const dialogId = useId();
	const titleId = useId();

	useEffect(() => {
		const dialog = dialogRef.current;
		if (!dialog) return;
		if (open && !dialog.open) {
			dialog.showModal();
		} else if (!open && dialog.open) {
			dialog.close();
		}
	}, [open]);

	// The page behind doesn't scroll while the panel is open.
	useEffect(() => {
		if (!open) return;
		const previousOverflow = document.body.style.overflow;
		document.body.style.overflow = "hidden";
		return () => {
			document.body.style.overflow = previousOverflow;
		};
	}, [open]);

	// A click on the dimmed page (the dialog itself, outside the panel) closes it.
	function handleClick(event: React.MouseEvent<HTMLDialogElement>) {
		if (event.target === event.currentTarget) setOpen(false);
	}

	const writing = digest.status === "streaming";

	return (
		<>
			<Button
				type="button"
				variant="secondary"
				aria-haspopup="dialog"
				aria-expanded={open}
				aria-controls={dialogId}
				onClick={() => setOpen(true)}
				className="fixed right-4 bottom-4 z-30 inline-flex items-center gap-2 shadow-soft sm:right-6 sm:bottom-6"
			>
				<Icon name="sparkles" />
				{/* Closed while an answer is being written: say so. */}
				{writing && !open ? "Writing…" : "Ask the AI"}
			</Button>

			<dialog
				id={dialogId}
				ref={dialogRef}
				aria-labelledby={titleId}
				onClose={() => setOpen(false)}
				onClick={handleClick}
				// Full screen on a phone, a 28rem panel on the right from sm up.
				// It slides in when it opens (starting: is the style it starts from).
				className="m-0 ml-auto h-dvh max-h-dvh w-full max-w-none bg-transparent p-0 transition-transform duration-300 ease-out backdrop:bg-black/40 starting:open:translate-x-full motion-reduce:transition-none sm:max-w-md"
			>
				<DigestPanel digest={digest} titleId={titleId} onClose={() => setOpen(false)} />
			</dialog>
		</>
	);
}
