import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { PasswordMatchForm, EmailForm, SignupForm } from "./exercise7";

describe("PasswordMatchForm", () => {
	it("shows an error when passwords don't match", () => {
		render(<PasswordMatchForm />);
		fireEvent.change(screen.getByLabelText("Password"), { target: { value: "abc123" } });
		fireEvent.change(screen.getByLabelText("Confirm password"), { target: { value: "abc124" } });
		fireEvent.click(screen.getByRole("button", { name: "Submit" }));
		expect(screen.getByRole("alert")).toHaveTextContent("Passwords do not match");
	});

	it("shows a success message when passwords match", () => {
		render(<PasswordMatchForm />);
		fireEvent.change(screen.getByLabelText("Password"), { target: { value: "abc123" } });
		fireEvent.change(screen.getByLabelText("Confirm password"), { target: { value: "abc123" } });
		fireEvent.click(screen.getByRole("button", { name: "Submit" }));
		expect(screen.getByText("Passwords match")).toBeInTheDocument();
	});
});

describe("EmailForm", () => {
	it("shows an error for an invalid email", () => {
		render(<EmailForm />);
		fireEvent.change(screen.getByLabelText("Email"), { target: { value: "not-an-email" } });
		fireEvent.click(screen.getByRole("button", { name: "Submit" }));
		expect(screen.getByRole("alert")).toHaveTextContent("Invalid email");
	});

	it("shows a success message for a valid email", () => {
		render(<EmailForm />);
		fireEvent.change(screen.getByLabelText("Email"), { target: { value: "jane@doe.com" } });
		fireEvent.click(screen.getByRole("button", { name: "Submit" }));
		expect(screen.getByText("Email OK")).toBeInTheDocument();
	});
});

describe("SignupForm", () => {
	let mockFetch: ReturnType<typeof vi.fn>;

	beforeEach(() => {
		mockFetch = vi.fn();
		vi.stubGlobal("fetch", mockFetch);
	});

	afterEach(() => {
		vi.unstubAllGlobals();
	});

	function fillValidForm() {
		fireEvent.change(screen.getByLabelText("Email"), { target: { value: "jane@doe.com" } });
		fireEvent.change(screen.getByLabelText("Password"), { target: { value: "abc123" } });
		fireEvent.change(screen.getByLabelText("Confirm password"), { target: { value: "abc123" } });
	}

	it("does not call the API when the form is invalid", () => {
		render(<SignupForm />);
		fireEvent.change(screen.getByLabelText("Email"), { target: { value: "not-an-email" } });
		fireEvent.click(screen.getByRole("button", { name: "Sign up" }));
		expect(screen.getByRole("alert")).toHaveTextContent("Invalid email");
		expect(mockFetch).not.toHaveBeenCalled();
	});

	it("sends the right payload to the API when the form is valid", () => {
		mockFetch.mockResolvedValue({ ok: true });
		render(<SignupForm />);
		fillValidForm();
		fireEvent.click(screen.getByRole("button", { name: "Sign up" }));
		expect(mockFetch).toHaveBeenCalledWith(
			"/api/register",
			expect.objectContaining({
				method: "POST",
				body: JSON.stringify({ email: "jane@doe.com", password: "abc123" }),
			}),
		);
	});

	it("shows a success message once the API call succeeds", async () => {
		mockFetch.mockResolvedValue({ ok: true });
		render(<SignupForm />);
		fillValidForm();
		fireEvent.click(screen.getByRole("button", { name: "Sign up" }));
		expect(await screen.findByText("Registration successful")).toBeInTheDocument();
	});

	it("shows an error message when the API call fails", async () => {
		mockFetch.mockResolvedValue({ ok: false });
		render(<SignupForm />);
		fillValidForm();
		fireEvent.click(screen.getByRole("button", { name: "Sign up" }));
		expect(await screen.findByRole("alert")).toHaveTextContent("Registration failed");
	});

	it("disables the submit button while the request is in flight", async () => {
		let resolvePromise: (value: { ok: boolean }) => void = () => {};
		mockFetch.mockReturnValue(new Promise((resolve) => { resolvePromise = resolve; }));
		render(<SignupForm />);
		fillValidForm();
		fireEvent.click(screen.getByRole("button", { name: "Sign up" }));
		expect(screen.getByRole("button", { name: "Sign up" })).toBeDisabled();
		resolvePromise({ ok: true });
		await screen.findByText("Registration successful");
	});
});
