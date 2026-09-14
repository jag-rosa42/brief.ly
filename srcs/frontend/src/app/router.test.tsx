import { describe, it, expect } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { AppRouter } from "@/app/router";
import { AuthProvider } from "@/app/AuthContext";

describe("AppRouter", () => {
	it("shows the landing page at /", () => {
		render(
			<MemoryRouter initialEntries={["/"]}>
				<AuthProvider>
					<AppRouter />
				</AuthProvider>
			</MemoryRouter>
		);
		expect(screen.getByRole("link", { name: "Terms Of Service" })).toBeInTheDocument();
	});

	it("navigates to Terms of Service via the footer link", () => {
		render(
			<MemoryRouter initialEntries={["/"]}>
				<AuthProvider>
					<AppRouter />
				</AuthProvider>
			</MemoryRouter>
		);
		fireEvent.click(screen.getByRole("link", { name: "Terms of Service" }));
		expect(screen.getByRole("heading", { name: "Terms of Service" })).toBeInTheDocument();
	});

	it("navigates to Privacy Policy via the footer link", () => {
		render(
			<MemoryRouter initialEntries={["/"]}>
				<AuthProvider>
					<AppRouter />
				</AuthProvider>
			</MemoryRouter>
		);
		fireEvent.click(screen.getByRole("link", { name: "Privacy Policy" }));
		expect(screen.getByRole("heading", { name: "Privacy Policy" })).toBeInTheDocument();
	});

	it("shows a 404 page for an unknown URL", () => {
		render(
			<MemoryRouter initialEntries={["/does-not-exist"]}>
				<AuthProvider>
					<AppRouter />
				</AuthProvider>
			</MemoryRouter>
		);
		expect(screen.getByText(/404/)).toBeInTheDocument();
	});
});
