import { render, screen } from "@testing-library/react";
import { expect, test } from "vitest";
import { Icon } from "@/shared/components/Icon";

test("is hidden from screen readers without a label", () => {
	render(<Icon name="close" data-testid="icon" />);

	expect(screen.getByTestId("icon")).toHaveAttribute("aria-hidden", "true");
});

test("is an image named by its label", () => {
	render(<Icon name="search" label="Search" />);

	expect(screen.getByRole("img", { name: "Search" })).toBeInTheDocument();
});

test("passes native svg attributes on to the svg", () => {
	render(<Icon name="check" data-testid="icon" aria-describedby="hint" />);

	expect(screen.getByTestId("icon")).toHaveAttribute("aria-describedby", "hint");
});
