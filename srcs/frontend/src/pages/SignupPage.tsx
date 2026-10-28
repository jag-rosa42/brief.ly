import { useState } from "react";
import type { SyntheticEvent } from "react";
import { useNavigate } from "react-router-dom";

import { Button } from "@/shared/components/Button";
import { Text } from "@/shared/components/Text";
import { useLocation } from "react-router-dom";
import { useAuth } from "@/app/useAuth";
import { Form } from "@/shared/components/Form";
import { Input } from "@/shared/components/Input";
import { Division } from "@/shared/components/Division";

import isEmail from "validator/lib/isEmail";

import { ApiError } from "@/shared/components/api/client";

interface SignupLocationState {
	message?: unknown;
}

function validateForm(email: string) {
	if (!isEmail(email)) {
		return "Enter a valid email address";
	}
	return null;
}

export function SignupPage() {
	const [password, setPassword] = useState("");
	const [confirmPass, setConfirmPass] = useState("");
	const [email, setEmail] = useState("");
	const [waiting, setWaiting] = useState(false);
	const navigate = useNavigate();
	const { signup } = useAuth();
	const location = useLocation();
	const navigationState = location.state as SignupLocationState | null;
	const initialMessage = typeof navigationState?.message === "string" ? navigationState.message : "";
	const [errorMessage, setErrorMessage] = useState(initialMessage);

	async function handleSubmit(e: SyntheticEvent) {
		e.preventDefault();
		if (waiting)
			return;
		setErrorMessage("");
		setWaiting(true);

		const error = validateForm(email.trim());

		if (error) {
			setErrorMessage(error);
			setWaiting(false);
			return;
		}
		if (password !== confirmPass) {
			setErrorMessage("Passwords do not match");
			setWaiting(false);
			return;
		}
		else if (password.length < 8) {
			setErrorMessage("Password must be at least 8 characters");
			setWaiting(false);
			return;
		}
		try {
			await signup(email.trim(), password);
			void navigate("/dashboard/profile");
		} catch (err) {
			if (err instanceof ApiError && err.code === "EMAIL_ALREADY_REGISTERED") {
				setErrorMessage("This email is already registered");
			} else if (err instanceof ApiError && err.code === "VALIDATION_ERROR") {
				setErrorMessage("Some fields are invalid, please check your input");
			} else if (err instanceof ApiError) {
				setErrorMessage("Something went wrong, please try again");
			} else {
				setErrorMessage("Unable to reach the server");
			}
		} finally {
			setWaiting(false);
		}
	}

	return (
		<Division variant="page">
			<Text variant="title" className="mb-10 text-center">
				Welcome !
			</Text>
			<div className="w-full max-w-sm">
				<Text variant="subheading" className="mb-4">
					Sign up
				</Text>
				<Division variant="featurecard" className="shadow-sm">
					<Form
						onSubmit={(e) => { void handleSubmit(e); }}
						actions={
							<div className="flex flex-col gap-3 w-full">
								{errorMessage && (
									<Text variant="error" role="alert">
										{errorMessage}
									</Text>
								)}
								<Button
									type="submit"
									variant="secondary"
									className="w-full"
									disabled={waiting}
								>
									{waiting ? "Signing up..." : "Sign up"}
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
						<Input
							variant="main"
							label="Confirm Password"
							name="confirmPass"
							type="password"
							onChange={(e) => setConfirmPass(e.target.value)}
						/>
					</Form>
				</Division>
			</div>
		</Division>
	);
}