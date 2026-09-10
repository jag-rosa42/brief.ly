import { useState } from "react";
import type { FormEvent } from "react";
import { Link } from "react-router-dom";


export function ProfilePage() {
	const [firstName, setFirstName] = useState("");
	const [preference1, setPreference1] = useState("");
	const [preference2, setPreference2] = useState("");
	const [preference3, setPreference3] = useState("");
	const [saved, setSaved] = useState(false);

	function handleSave(e: FormEvent) {
		e.preventDefault();
		setSaved(true);
	}

	return (
		<main className="max-w-2xl mx-auto px-6 py-16">
			<h1 className="text-3xl font-bold text-primary mb-6">Profile</h1>

			<form className="flex flex-col gap-4" onSubmit={handleSave}>
				<label className="flex flex-col gap-1">
					Prénom
					<input
						type="text"
						value={firstName}
						onChange={(e) => setFirstName(e.target.value)}
						className="border rounded px-3 py-2"
					/>
				</label>

				<label className="flex flex-col gap-1">
					Préférence 1
					<input
						type="text"
						value={preference1}
						onChange={(e) => setPreference1(e.target.value)}
						className="border rounded px-3 py-2"
					/>
				</label>

				<label className="flex flex-col gap-1">
					Préférence 2
					<input
						type="text"
						value={preference2}
						onChange={(e) => setPreference2(e.target.value)}
						className="border rounded px-3 py-2"
					/>
				</label>

				<label className="flex flex-col gap-1">
					Préférence 3
					<input
						type="text"
						value={preference3}
						onChange={(e) => setPreference3(e.target.value)}
						className="border rounded px-3 py-2"
					/>
				</label>

				<button
					type="submit"
					className="bg-primary text-white rounded px-4 py-2 self-start"
				>
					Save
				</button>
				<Link to="/"
					type="submit"
					className="bg-primary text-white rounded px-4 py-2 self-start"
				>
					Back
				</Link>

				{saved && <p className="text-green-600">Profile Saved</p>}
			</form>
		</main>
	);
}
