import { useState } from "react";
import type { SyntheticEvent } from "react";
import { useNavigate } from "react-router-dom";
import { Link } from "react-router-dom"

export function SignupPage() {


	const [pass1, setPass1] = useState("");
	const [pass2, setPass2] = useState("");
	const [email, setEmail] = useState("");
	const [error, setError] = useState("");
	const [waiting, setWaiting] = useState(false);
	const navigate = useNavigate();

	async function handleSubmit(e: SyntheticEvent)
	{
		e.preventDefault();
		setWaiting(true);
		if (email === "")
		{
			setError("Email is required");
			setWaiting(false);
			return;
		}
		if (!email.includes("@"))
		{
			setError("Enter a valid email address");
			setWaiting(false);
			return;
		}
		else if (pass1.length < 8)
		{
			setError("Password must be at least 8 characters");
			setWaiting(false);
			return;
		}
		else if (pass1 !== pass2)
		{
			setError("Passwords do not match");
			setWaiting(false);
			return;
		}
		navigate("/login", { state: { message: "Account created! You can now log in." } });
		setWaiting(false);
	}

	return (
	<main className="max-w-md mx-auto px-6 py-16">
		<h1 className="text-center font-serif text-4xl font-bold text-accent-dark mb-16">Welcome!</h1>
		<h2 className="font-sans text-3xl font-bold text-accent-dark mb-6">Sign up</h2>
		<form  onSubmit={handleSubmit}className="flex rounded flex-col gap-4">
			<div className="bg-white border border-ui rounded-xl p-6">
			<label className="flex flex-col gap-2">
				Email:
			<input type="email" className="border border-ui rounded-md px-3 py-2 bg-white focus:outline-none focus:ring-2 focus:ring-primary" onChange={(e) => setEmail(e.target.value)}></input>
			</label>
			<label className="flex flex-col gap-1">
			Password
			<input type="password" className="focus:outline-none focus:ring-2 focus:ring-primary" onChange={(e) => setPass1(e.target.value)}></input>
			</label>
			<label className="flex flex-col gap-1">
			Confirm password
			<input type="password" className="focus:outline-none focus:ring-2 focus:ring-primary" onChange={(e) => setPass2(e.target.value)}></input>
			</label>
			<p role="alert">{error}</p>
			</div>
			<button type="submit" className="bg-primary text-background rounded px-4 py-2 hover:bg-primary-dark disabled:opacity-50" disabled={waiting}>Sign up</button>
		</form>
			<Link to="/"
				className="bg-primary text-white rounded px-4 py-2 self-start"
			>
				Back
			</Link>
		</main>
	);
}
