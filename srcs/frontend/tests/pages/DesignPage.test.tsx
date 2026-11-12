import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { expect, test } from "vitest";
import { NotificationProvider } from "@/app/NotificationContext";
import { DesignPage } from "@/pages/DesignPage";
import { ICON_NAMES } from "@/shared/components/iconPaths";

function renderPage() {
	render(
		<MemoryRouter>
			<NotificationProvider>
				<DesignPage />
			</NotificationProvider>
		</MemoryRouter>,
	);
}

test("shows every section of the design system", () => {
	renderPage();

	const sections = screen.getAllByRole("heading", { level: 2 }).map((h) => h.textContent);
	for (const title of [
		"Colors",
		"Typography",
		"Icons",
		"Surfaces",
		"Buttons and links",
		"Forms",
		"Tabs",
		"Cards",
	]) {
		expect(sections).toContain(title);
	}
});

test("shows every icon", () => {
	renderPage();

	for (const name of ICON_NAMES) {
		expect(screen.getByText(name)).toBeInTheDocument();
	}
});

test("shows every relief of the neomorphic appearance", () => {
	renderPage();

	expect(screen.getByText("up").parentElement).toHaveClass("shadow-relief-up");
	expect(screen.getByText("down").parentElement).toHaveClass("shadow-relief-down");
	expect(screen.getByText("neomorphic")).toBeInTheDocument();
});

test("shows a notification of the chosen kind", () => {
	renderPage();

	fireEvent.click(screen.getAllByRole("button", { name: "Show" })[2]);

	// The error input of the page is an alert too: find the notification by its text.
	expect(screen.getByText("Example notification (error).").parentElement).toHaveAttribute(
		"role",
		"alert",
	);
});

test("keeps one main heading: the Text samples are not headings", () => {
	renderPage();

	expect(screen.getAllByRole("heading", { level: 1 })).toHaveLength(1);
});
