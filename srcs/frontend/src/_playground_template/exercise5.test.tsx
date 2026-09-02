import { describe, it, expect } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { AppRoutes } from "./exercise5";

describe("AppRoutes", () => {
	it("shows the home page at /", () => {
		render(
			<MemoryRouter initialEntries={["/"]}>
				<AppRoutes />
			</MemoryRouter>
		);
		expect(screen.getByRole("heading", { name: "Home" })).toBeInTheDocument();
	});

	it("navigates to the about page when clicking the About link", () => {
		render(
			<MemoryRouter initialEntries={["/"]}>
				<AppRoutes />
			</MemoryRouter>
		);
		fireEvent.click(screen.getByRole("link", { name: "About" }));
		expect(screen.getByRole("heading", { name: "About" })).toBeInTheDocument();
		expect(
			screen.queryByRole("heading", { name: "Home" })
		).not.toBeInTheDocument();
	});

	it("shows the 404 page for an unknown URL", () => {
		render(
			<MemoryRouter initialEntries={["/does-not-exist"]}>
				<AppRoutes />
			</MemoryRouter>
		);
		expect(screen.getByRole("heading", { name: "404" })).toBeInTheDocument();
	});
});
