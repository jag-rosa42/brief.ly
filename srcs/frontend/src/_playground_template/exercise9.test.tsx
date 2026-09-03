import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { Heading, Text, Section } from "./exercise9";

describe("Heading", () => {
	it("renders an <h1> when level is 1", () => {
		render(<Heading level={1}>Title</Heading>);
		expect(screen.getByRole("heading", { level: 1, name: "Title" })).toBeInTheDocument();
	});

	it("renders an <h2> when level is 2", () => {
		render(<Heading level={2}>Subtitle</Heading>);
		expect(screen.getByRole("heading", { level: 2, name: "Subtitle" })).toBeInTheDocument();
	});

	it("renders an <h3> when level is 3", () => {
		render(<Heading level={3}>Sub-subtitle</Heading>);
		expect(screen.getByRole("heading", { level: 3, name: "Sub-subtitle" })).toBeInTheDocument();
	});
});

describe("Text", () => {
	it("renders its children", () => {
		render(<Text>Some paragraph text</Text>);
		expect(screen.getByText("Some paragraph text")).toBeInTheDocument();
	});
});

describe("Section", () => {
	it("renders the title as an <h2> and the children as text", () => {
		render(<Section title="Cookies">We use cookies.</Section>);
		expect(screen.getByRole("heading", { level: 2, name: "Cookies" })).toBeInTheDocument();
		expect(screen.getByText("We use cookies.")).toBeInTheDocument();
	});
});
