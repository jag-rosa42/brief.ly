import { fireEvent, render, screen } from "@testing-library/react";
import { expect, test, vi } from "vitest";
import { Division } from "@/shared/components/Division";
import { Tabs } from "@/shared/components/Tab";
import { ArticleCard } from "@/shared/components/ArticleCard";

test("a dashboard card switches between its classic and neomorphic surfaces", () => {
	const { rerender } = render(<Division variant="dashboardcard" data-testid="card" />);
	const card = screen.getByTestId("card");
	expect(card).toHaveClass("bg-white/60", "shadow-soft");
	expect(card).not.toHaveClass("shadow-relief-up");

	rerender(<Division variant="dashboardcard" appearance="neomorphic" data-testid="card" />);
	expect(card).toHaveClass("bg-background", "shadow-relief-up");
	expect(card).not.toHaveClass("bg-white/60", "shadow-soft");
});

test("pill tabs keep the chosen appearance when selection changes", () => {
	const tabs = [
		{ value: "first", label: "First", content: "First panel" },
		{ value: "second", label: "Second", content: "Second panel" },
	];
	const { rerender } = render(<Tabs tabs={tabs} variant="pill" />);
	const group = screen.getByRole("tablist");
	const first = screen.getByRole("tab", { name: "First" });
	const second = screen.getByRole("tab", { name: "Second" });
	expect(group).not.toHaveClass("shadow-relief-up");
	expect(first).toHaveClass("shadow-sm");

	rerender(<Tabs tabs={tabs} variant="pill" appearance="neomorphic" />);
	expect(group).toHaveClass("shadow-relief-up");
	expect(first).toHaveClass("shadow-relief-down");
	expect(second).not.toHaveClass("shadow-relief-down");

	fireEvent.click(second);
	expect(first).not.toHaveClass("shadow-relief-down");
	expect(second).toHaveClass("shadow-relief-down");
});

test("article cards pass their appearance to the surface", () => {
	const article = {
		id: "article-1",
		title: "A story",
		category: "science",
		source: "News",
		url: null,
		summary: "A summary",
	};
	const props = { article, isSaved: false, onReadMore: vi.fn(), onToggleSave: vi.fn() };
	const { rerender } = render(<ArticleCard {...props} />);
	const card = screen.getByText("A story").parentElement;
	expect(card).toHaveClass("bg-white/60", "shadow-sm");

	rerender(<ArticleCard {...props} appearance="neomorphic" />);
	expect(card).toHaveClass("bg-background", "shadow-relief-up", "hover:shadow-relief-up-hover");
	expect(card).not.toHaveClass("shadow-sm");
});
