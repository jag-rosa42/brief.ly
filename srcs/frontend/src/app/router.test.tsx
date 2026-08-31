import { describe, it, expect } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { AppRouter } from "./router";

describe("AppRouter", () => {
	it("shows the landing page at /", () => {
		render(
			<MemoryRouter initialEntries={["/"]}>
				<AppRouter />
			</MemoryRouter>
		);
		expect(screen.getByRole("link", { name: "About Us" })).toBeInTheDocument();
	});

	it("navigates to About Us via the footer link", () => {
		render(
			<MemoryRouter initialEntries={["/"]}>
				<AppRouter />
			</MemoryRouter>
		);
		fireEvent.click(screen.getByRole("link", { name: "About Us" }));
		expect(screen.getByRole("heading", { name: "About Us" })).toBeInTheDocument();
	});

	it("navigates to Privacy via the footer link", () => {
		render(
			<MemoryRouter initialEntries={["/"]}>
				<AppRouter />
			</MemoryRouter>
		);
		fireEvent.click(screen.getByRole("link", { name: "Privacy" }));
		expect(screen.getByRole("heading", { name: "Privacy" })).toBeInTheDocument();
	});

	it("shows a 404 page for an unknown URL", () => {
		render(
			<MemoryRouter initialEntries={["/does-not-exist"]}>
				<AppRouter />
			</MemoryRouter>
		);
		expect(screen.getByText(/404/)).toBeInTheDocument();
	});
});
