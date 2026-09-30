import { useState } from "react";
import type { SyntheticEvent } from "react";
import { useNavigate } from "react-router-dom";

import { Button } from "@/shared/components/Button";
import { Card } from "@/shared/components/Card";
import { Text } from "@/shared/components/Text";
import { useLocation } from "react-router-dom";
import { useAuth } from "@/app/AuthContext";
import { Form } from "@/shared/components/Form";
import { Input } from "@/shared/components/Input";


export function SignupPage() {
	const [pass, setPassword] = useState("");
	const [confirmPass, setConfirmPass] = useState("");
	const [email, setEmail] = useState("");
	const [waiting, setWaiting] = useState(false);
	const navigate = useNavigate();
	const { login } = useAuth();
	const location = useLocation();
	const [result, setResult] = useState(
	location.state?.message ? <p>{location.state.message}</p> : <p></p>);


	async function handleSubmit(e: SyntheticEvent)
	{
		e.preventDefault();
		setWaiting(true);
		if (email == "")
		{
			setResult(<p role="alert" className="text-error">Email is required</p>);
			setWaiting(false);
			return;
		}
		if (!email.includes("@"))
		{
			setResult(<p role="alert" className="text-error">Enter a valid email address</p>);
			setWaiting(false);
			return;
		}
		if (pass !== confirmPass)
		{
			setResult(<p role="alert" className="text-error">Password do not match</p>);
			setWaiting(false);
			return;
		}
		else if (pass.length < 8)
		{
			setResult(<p role="alert" className="text-error">Password must be at least 8 characters</p>);
			setWaiting(false);
			return;
		}
		//TODO add call API (mock behaviour here)
		try {
			await login();
			navigate("/profile");
		} catch (err) {
			setResult(<p role="alert" className="text-error"> Registration failed</p>);
		}
		finally {
		setWaiting(false);
		}
	}

	return(
		<div className="min-h-screen bg-background flex flex-col items-center pt-12 px-4">
			<Text variant="title" className="mb-10 text-center">
				Welcome !
			</Text>
			<div className="w-full max-w-sm">
				<Text variant="subheading" className="mb-4">
					Sign up
				</Text>
				<Card>
					<Form
					onSubmit={handleSubmit}
					actions={
						<div className="flex flex-col gap-3 w-full">
							{result}
							<Button
								type="submit"
								variant="secondary"
								className="w-full"
								disabled={waiting}>
								{waiting ? "Signing in..." : "Sign in"}
							</Button>
						</div>
							}
							>
						<Input
							variant="main"
							label="Email"
							name="email"
							type="email"
							onChange={(e) => setEmail(e.target.value)}/>
						<Input
							variant="main"
							label="Password"
							name="password"
							type="password"
							onChange={(e) => setPassword(e.target.value)}/>
						<Input
							variant="main"
							label="Confirm Password"
							name="confirmPass"
							type="password"
							onChange={(e) => setConfirmPass(e.target.value)}/>
					</Form>
				</Card>
			</div>
		</div>
	)
}