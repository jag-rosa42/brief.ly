import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { ThemedButton, FormField, CardGrid } from "./exercise8";

describe("ThemedButton", () => {
	it("renders its children for the primary variant", () => {
		render(<ThemedButton variant="primary">Sign up</ThemedButton>);
		expect(screen.getByRole("button", { name: "Sign up" })).toBeInTheDocument();
	});

	it("renders its children for the outline variant", () => {
		render(<ThemedButton variant="outline">Cancel</ThemedButton>);
		expect(screen.getByRole("button", { name: "Cancel" })).toBeInTheDocument();
	});
});

describe("FormField", () => {
	it("shows the label and current value", () => {
		render(<FormField label="Email" value="jane@doe.com" onChange={() => {}} />);
		expect(screen.getByLabelText("Email")).toHaveValue("jane@doe.com");
	});

	it("calls onChange with the new value when typed into", () => {
		const handleChange = vi.fn();
		render(<FormField label="Email" value="" onChange={handleChange} />);
		fireEvent.change(screen.getByLabelText("Email"), { target: { value: "a@b.com" } });
		expect(handleChange).toHaveBeenCalledWith("a@b.com");
	});
});

describe("CardGrid", () => {
	it("renders all its children", () => {
		render(
			<CardGrid>
				<p>Card one</p>
				<p>Card two</p>
				<p>Card three</p>
			</CardGrid>,
		);
		expect(screen.getByText("Card one")).toBeInTheDocument();
		expect(screen.getByText("Card two")).toBeInTheDocument();
		expect(screen.getByText("Card three")).toBeInTheDocument();
	});
});
