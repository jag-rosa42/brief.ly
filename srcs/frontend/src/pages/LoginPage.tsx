import { useState } from "react";
import type { SyntheticEvent } from "react";
import { useNavigate } from "react-router-dom";
import { useLocation } from "react-router-dom";
import { useAuth } from "@/app/AuthContext";

export function LoginPage() {


	const [pass, setP1] = useState("");
	const [email, setEmail] = useState("");
	const [waiting, setWaiting] = useState(false);
	const navigate = useNavigate();
	const { login } = useAuth();
	const location = useLocation();
	const [result, setResult] = useState(
	location.state?.message ? <p>{location.state.message}</p> : <p></p>);
	

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
		else if (pass.length < 8)
		{
			setResult(<p role="alert">Password must be at least 8 characters</p>);
			setWaiting(false);
			return;
		}
		login();
		navigate("/");
		setWaiting(false);
	}

	async function oauth(){
		setWaiting(true);
		login();
		navigate("/");
		setWaiting(false);
	}

	return (
	<main className="max-w-md mx-auto px-6 py-16">
		<h1 className="text-center font-serif text-4xl font-bold text-accent-dark mb-16">Welcome back!</h1>
		<h2 className="font-sans text-3xl font-bold text-accent-dark mb-6">Log in</h2>
		<div className="flex flex-col gap-3">
		<form  onSubmit={handleSubmit}className="flex rounded flex-col gap-4">
			<div className="bg-white border border-ui rounded-xl p-6">
			<label className="flex flex-col gap-2">
				Email:
			<input type="email" className="border border-ui rounded-md px-3 py-2 bg-white focus:outline-none focus:ring-2 focus:ring-primary" onChange={(e) => setEmail(e.target.value)} />
			</label>
			<label className="flex flex-col gap-2">
				Password:
			<input type="password" className="border border-ui rounded-md px-3 py-2 bg-white focus:outline-none focus:ring-2 focus:ring-primary" onChange={(e) => setP1(e.target.value)}
			/>
			</label>
			{result}
			</div>
			<button type="submit" className="w-full bg-primary text-background rounded px-4 py-2 hover:text-secondary disabled:opacity-50" disabled={waiting}>Log in</button>
		</form>
			<button onClick={oauth} type="button" className="w-full bg-primary text-background rounded px-4 py-2 hover:text-secondary disabled:opacity-50" disabled={waiting}>OAuth</button>
			</div>
		</main>
	);
}
