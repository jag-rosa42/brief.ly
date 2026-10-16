import { useState } from "react";
import type { SyntheticEvent } from "react";
import { useNavigate } from "react-router-dom";

import { useLocation } from "react-router-dom";
import { useAuth } from "@/app/useAuth";
import { Form } from "@/shared/components/Form";
import { Input } from "@/shared/components/Input";

import { Button } from "@/shared/components/Button";
import { Text } from "@/shared/components/Text";
import { Division } from "@/shared/components/Division";

import isEmail from "validator/lib/isEmail";

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
	const navigate = useNavigate();
	const { login } = useAuth();
	const location = useLocation();
	
	const navigationState = location.state as LoginLocationState | null;
	const initialMessage = typeof navigationState?.message === "string" ? navigationState.message : "";
	const [errorMessage, setErrorMessage] = useState(initialMessage);
	
	function handleSubmit(e: SyntheticEvent) {
		e.preventDefault();
		setErrorMessage("");
		//setWaiting(true);

		const error = validateForm(email);

		if (error) {
    		setErrorMessage(error);
			//setWaiting(false);
    		return;
		}
		if (password === "") {
			setErrorMessage("Password is required");
			//setWaiting(false);
			return;
		}
		//TODO add call API (mock behaviour here)
		try {
			login();
			void navigate("/dashboard/brief");
		} catch {
			setErrorMessage("Login failed. Please try again");
		} finally {
			setWaiting(false);
		}
	}


	return(
		<Division variant = "page">
			<Text variant="title" className="mb-10 text-center">
				Welcome back!
			</Text>
			<div className="w-full max-w-sm">
				<Text variant="subheading" className="mb-4">
					Log in
				</Text>
				<Division variant="featurecard" className="shadow-sm">
					<Form
					onSubmit={handleSubmit}
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

