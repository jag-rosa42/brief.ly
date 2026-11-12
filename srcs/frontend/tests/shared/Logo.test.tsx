import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { expect, test } from "vitest";
import { Logo } from "@/shared/components/Logo";

test("shows the logo image next to the app name, linking home", () => {
	render(
		<MemoryRouter>
			<Logo />
		</MemoryRouter>,
	);

	// The link's accessible name is the text only: the image is decorative.
	const link = screen.getByRole("link", { name: "Brief.ly" });
	expect(link).toHaveAttribute("href", "/");
	expect(link.querySelector("img")).toHaveAttribute("src", "/favicon.svg");
});
