import { act, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, expect, test, vi } from "vitest";
import { NotificationProvider } from "@/app/NotificationContext";
import { useNotify } from "@/app/useNotify";

// useNotify is a hook: a tiny component calls it, like a page would.
function NotifyButton({ message }: { message: string }) {
	const { notify } = useNotify();
	return <button onClick={() => notify(message, "success")}>{message}</button>;
}

afterEach(() => {
	vi.useRealTimers();
});

test("gives a new notification its full duration", () => {
	vi.useFakeTimers();
	render(
		<NotificationProvider>
			<NotifyButton message="First" />
			<NotifyButton message="Second" />
		</NotificationProvider>,
	);

	fireEvent.click(screen.getByRole("button", { name: "First" }));
	act(() => {
		vi.advanceTimersByTime(3000);
	});
	fireEvent.click(screen.getByRole("button", { name: "Second" }));
	act(() => {
		vi.advanceTimersByTime(3000);
	});

	// The second one has only been shown for 3 s out of 4: it must still be there.
	expect(screen.getByRole("status")).toHaveTextContent("Second");

	act(() => {
		vi.advanceTimersByTime(1000);
	});
	expect(screen.queryByRole("status")).not.toBeInTheDocument();
});
