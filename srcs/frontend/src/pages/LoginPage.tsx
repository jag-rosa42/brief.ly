import { useState } from "react";
import type { SyntheticEvent } from "react";

import { useLocation } from "react-router-dom";
import { useAuth } from "@/app/useAuth";
import { Form } from "@/shared/components/Form";
import { Input } from "@/shared/components/Input";

import { Button } from "@/shared/components/Button";
import { Text } from "@/shared/components/Text";
import { Division } from "@/shared/components/Division";

import isEmail from "validator/lib/isEmail";
import { ApiError } from "@/shared/components/api/client";
import { useNotify } from "@/app/useNotify";

interface LoginLocationState {
	message?: unknown;
}

function validateForm(email: string) {
	if (!isEmail(email)) {
		return "Enter a valid email address";
	}
	return null;
}

export function LoginPage() {
	const [password, setPassword] = useState("");
	const [email, setEmail] = useState("");
	const [waiting, setWaiting] = useState(false);
	const { login } = useAuth();
	const { notify } = useNotify();
	const location = useLocation();

	const navigationState = location.state as LoginLocationState | null;
	const initialMessage =
		typeof navigationState?.message === "string" ? navigationState.message : "";
	const [errorMessage, setErrorMessage] = useState(initialMessage);

	async function handleSubmit(e: SyntheticEvent) {
		e.preventDefault();
		if (waiting) return;
		setErrorMessage("");
		setWaiting(true);

		const error = validateForm(email.trim());

		if (error) {
			setErrorMessage(error);
			setWaiting(false);
			return;
		}
		if (password === "") {
			setErrorMessage("Password is required");
			setWaiting(false);
			return;
		}
		try {
			await login(email.trim(), password);
			notify("Logged in successfully", "success");
		} catch (err) {
			if (err instanceof ApiError && err.code === "INVALID_CREDENTIALS") {
				setErrorMessage("Invalid email or password");
			} else if (err instanceof ApiError && err.code === "VALIDATION_ERROR") {
				setErrorMessage("Some fields are invalid, please check your input");
			} else if (err instanceof ApiError && err.status === 429) {
				// The gateway's limit on login attempts (plain text, so no code).
				setErrorMessage("Too many attempts, please wait a minute and try again");
			} else if (err instanceof ApiError) {
				notify("Something went wrong, please try again", "error");
			} else {
				notify("Unable to reach the server", "error");
			}
		} finally {
			setWaiting(false);
		}
	}

	return (
		<Division variant="page">
			<Text variant="title" className="mb-10 text-center">
				Welcome back!
			</Text>
			<div className="w-full max-w-sm">
				<Text variant="subheading" className="mb-4">
					Log in
				</Text>
				<Division variant="featurecard" className="shadow-sm">
					<Form
						onSubmit={(e) => {
							void handleSubmit(e);
						}}
						actions={
							<div className="flex flex-col gap-3 w-full">
								{errorMessage && (
									<Text variant="error" role="alert">
										{errorMessage}
									</Text>
								)}
								<Button type="submit" variant="secondary" className="w-full" disabled={waiting}>
									{waiting ? "Logging in..." : "Log in"}
								</Button>
							</div>
						}
					>
						<Input
							variant="main"
							label="Email address (name@example.com)"
							name="email"
							type="email"
							onChange={(e) => setEmail(e.target.value)}
						/>
						<Input
							variant="main"
							label="Password"
							name="password"
							type="password"
							onChange={(e) => setPassword(e.target.value)}
						/>
					</Form>
				</Division>
			</div>
		</Division>
	);
}
