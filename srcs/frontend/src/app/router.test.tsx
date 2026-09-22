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
		expect(screen.getByRole("link", { name: "Terms of Service" })).toBeInTheDocument();
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
		const main = screen.getAllByRole("main")[1];
		expect(main).toHaveTextContent("Terms of Service");
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
		const main = screen.getAllByRole("main")[1];
		expect(main).toHaveTextContent("Privacy Policy");
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
