import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { Greeting, Counter, UserCard, ProductList, Badge } from "./exercise3";

describe("Greeting", () => {
	it("greets by name", () => {
		render(<Greeting name="Alice" />);
		expect(screen.getByText("Hello, Alice!")).toBeInTheDocument();
	});
});

describe("Counter", () => {
	it("shows the count", () => {
		render(<Counter count={3} />);
		expect(screen.getByText("Count: 3")).toBeInTheDocument();
	});
});

describe("UserCard", () => {
	it("shows name and email", () => {
		render(<UserCard user={{ name: "Bob", email: "bob@example.com" }} />);
		expect(screen.getByText("Bob")).toBeInTheDocument();
		expect(screen.getByText("bob@example.com")).toBeInTheDocument();
	});
});

describe("ProductList", () => {
	it("renders one item per product", () => {
		render(
			<ProductList
				products={[
					{ id: 1, name: "Riz" },
					{ id: 2, name: "Pates" },
				]}
			/>
		);
		expect(screen.getByText("Riz")).toBeInTheDocument();
		expect(screen.getByText("Pates")).toBeInTheDocument();
		expect(screen.getAllByRole("listitem")).toHaveLength(2);
	});
});

describe("Badge", () => {
	it("renders its children", () => {
		render(<Badge>New</Badge>);
		expect(screen.getByText("New")).toBeInTheDocument();
	});
});
