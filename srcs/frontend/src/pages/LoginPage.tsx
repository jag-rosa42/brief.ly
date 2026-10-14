import { useState } from "react";
import type { SyntheticEvent } from "react";
import { useNavigate } from "react-router-dom";

import { useLocation } from "react-router-dom";
import { useAuth } from "@/app/AuthContext";
import { Form } from "@/shared/components/Form";
import { Input } from "@/shared/components/Input";

import { Button } from "@/shared/components/Button";
import { Text } from "@/shared/components/Text";
import { Division } from "@/shared/components/Division";

import isEmail from "validator/lib/isEmail";

function validateForm(email: string) {
	if (!isEmail(email)) {
		return "Enter a valid email address";
	}
	return null;
}

export function LoginPage() {
	const [pass, setPassword] = useState("");
	const [email, setEmail] = useState("");
	const [waiting, setWaiting] = useState(false);
	const navigate = useNavigate();
	const { login } = useAuth();
	const location = useLocation();
	const [errorMessage, setErrorMessage] = useState<string>(location.state?.message ?? "");

	async function handleSubmit(e: SyntheticEvent) {
		e.preventDefault();
		setErrorMessage("");
		setWaiting(true);

		const error = validateForm(email);

		if (error) {
    		setErrorMessage(error);
			setWaiting(false);
    		return;
		}
		if (pass === "") {
			setErrorMessage("Password is required");
			setWaiting(false);
			return;
		}
		//TODO add call API (mock behaviour here)
		try {
			await login();
			navigate("/sidebar/brief");
		} catch (err) {
			setErrorMessage("Login failed. Please try again");
		} finally {
			setWaiting(false);
		}
	}

	async function oauth() {
		setWaiting(true);
		login();
		navigate("*");
		setWaiting(false);
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

								<Button
									type="button"
									variant="primary"
									className="w-full"
									onClick={oauth}
									disabled={waiting}
								>
									OAuth
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

