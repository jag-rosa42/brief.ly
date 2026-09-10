import { useState } from "react";
import type { SyntheticEvent } from "react";
import { useNavigate } from "react-router-dom";

export function SignupPage() {


	const [p1, setP1] = useState("");
	const [p2, setP2] = useState("");
	const [email, setEmail] = useState("");
	const [result, setResult] = useState(<p></p>);
	const [waiting, setWaiting] = useState(false);
	const navigate = useNavigate();

	async function handleSubmit(e: SyntheticEvent)
	{
		setWaiting(true);
		e.preventDefault();
		if (email == "")
		{
			setResult(<p role="alert">Email is required</p>);
			setWaiting(false);
			return;
		}
		if (!email.includes("@"))
		{
			setResult(<p role="alert">Enter a valid email address</p>);
			setWaiting(false);
			return;
		}
		else if (p1.length < 8)
		{
			setResult(<p role="alert">Password must be at least 8 characters</p>);
			setWaiting(false);
			return;
		}
		else if (p1 != p2)
		{
			setResult(<p role="alert">Passwords do not match</p>);
			setWaiting(false);
			return;
		}
		navigate("/login", { state: { message: "Account created! You can now log in." } });
		setWaiting(false);
	}

	return (
	<main className="max-w-md mx-auto px-6 py-16">
		<h1 className="text-3xl font-bold text-primary mb-6">Sign up</h1>
		<form  onSubmit={handleSubmit}className="flex rounded bg-accent flex-col gap-4">
			<label className="flex flex-col gap-1">
			Email
			<input type="string" className="focus:outline-none focus:ring-2 focus:ring-primary" onChange={(e) => setEmail(e.target.value)}></input>
			</label>
			<label className="flex flex-col gap-1">
			Password
			<input type="password" className="focus:outline-none focus:ring-2 focus:ring-primary" onChange={(e) => setP1(e.target.value)}></input>
			</label>
			<label className="flex flex-col gap-1">
			Confirm password
			<input type="password" className="focus:outline-none focus:ring-2 focus:ring-primary" onChange={(e) => setP2(e.target.value)}></input>
			</label>
			{result}
			<button type="submit" className="bg-primary text-background rounded px-4 py-2 hover:bg-primary-dark disabled:opacity-50" disabled={waiting}>Sign up</button>
		</form>
		</main>
	);

	return null;
}
