import { describe, it, expect } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { ToggleButton, Counter, TextEcho, ItemList, LikeButton } from "./exercise4";

describe("ToggleButton", () => {
	it("toggles its text on click", () => {
		render(<ToggleButton />);
		const button = screen.getByRole("button");
		expect(button).toHaveTextContent("Show");
		fireEvent.click(button);
		expect(button).toHaveTextContent("Hide");
		fireEvent.click(button);
		expect(button).toHaveTextContent("Show");
	});
});

describe("Counter", () => {
	it("increments on click", () => {
		render(<Counter />);
		expect(screen.getByText("Count: 0")).toBeInTheDocument();
		fireEvent.click(screen.getByRole("button", { name: "+1" }));
		fireEvent.click(screen.getByRole("button", { name: "+1" }));
		expect(screen.getByText("Count: 2")).toBeInTheDocument();
	});
});

describe("TextEcho", () => {
	it("echoes what's typed", () => {
		render(<TextEcho />);
		const input = screen.getByRole("textbox");
		fireEvent.change(input, { target: { value: "Hello" } });
		expect(screen.getByText("Hello")).toBeInTheDocument();
	});
});

describe("ItemList", () => {
	it("shows the initial items", () => {
		render(<ItemList initialItems={["Riz", "Pates"]} />);
		expect(screen.getByText("Riz")).toBeInTheDocument();
		expect(screen.getByText("Pates")).toBeInTheDocument();
	});

	it("shows 'No items' after clearing", () => {
		render(<ItemList initialItems={["Riz", "Pates"]} />);
		fireEvent.click(screen.getByRole("button", { name: "Clear" }));
		expect(screen.getByText("No items")).toBeInTheDocument();
		expect(screen.queryByText("Riz")).not.toBeInTheDocument();
	});
});

describe("LikeButton", () => {
	it("switches from Like to Liked, and stays Liked", () => {
		render(<LikeButton />);
		const button = screen.getByRole("button");
		expect(button).toHaveTextContent("Like");
		fireEvent.click(button);
		expect(button).toHaveTextContent("Liked");
		fireEvent.click(button);
		expect(button).toHaveTextContent("Liked");
	});
});
