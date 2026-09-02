import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { Card, Alert, PrimaryButton } from "./exercise6";

describe("Card", () => {
	it("shows the title and description", () => {
		render(<Card title="Coffee" description="A strong espresso" />);
		expect(screen.getByText("Coffee")).toBeInTheDocument();
		expect(screen.getByText("A strong espresso")).toBeInTheDocument();
	});
});

describe("Alert", () => {
	it("uses a green-ish background for success", () => {
		render(<Alert type="success" message="Saved!" />);
		const alert = screen.getByRole("alert");
		expect(alert).toHaveTextContent("Saved!");
		expect(alert.className).toMatch(/green/);
	});

	it("uses a red-ish background for error", () => {
		render(<Alert type="error" message="Something broke" />);
		const alert = screen.getByRole("alert");
		expect(alert).toHaveTextContent("Something broke");
		expect(alert.className).toMatch(/red/);
	});
});

describe("PrimaryButton", () => {
	it("renders its children as a button", () => {
		render(<PrimaryButton>Submit</PrimaryButton>);
		expect(screen.getByRole("button", { name: "Submit" })).toBeInTheDocument();
	});
});
