import { useState } from "react";
import type { ChangeEvent, SyntheticEvent } from "react";
import { Link } from "react-router-dom";


export function ProfilePage() {
	const [profile, setProfile] = useState({
    firstName: "",
    preference1: "",
    preference2: "",
    preference3: "",
    interest1: "",
    interest2: "",
    interest3: "",
    focusTime: "",
    password: "",
    confirmPassword: "",
	});
	const [saved, setSaved] = useState(false);
	function handleSave(e: SyntheticEvent) {
		e.preventDefault();
		setSaved(true);
	}

	const handleChange = (e: ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;

    setProfile((prev) => ({
        ...prev,
        [name]: value,
    }));
};

	return (
		<main className="max-w-2xl mx-auto px-6 py-16">
			<h1 className="text-3xl font-bold text-primary mb-6">Profile</h1>

			<form className="flex flex-col gap-4" onSubmit={handleSave}>
				<label className="flex flex-col gap-1">
					Last name:
					<input
						type="text"
						name="firstName"
						value={profile.firstName}
						onChange={handleChange}
						className="border rounded px-3 py-2"
					/>
				</label>

				<label className="flex flex-col gap-1">
					First name:
					<input
						type="text"
						name="preference1"
						value={profile.preference1}
						onChange={handleChange}
						className="border rounded px-3 py-2"
					/>
				</label>

				<label className="flex flex-col gap-1">
					Email:
					<input
						type="text"
						name="preference2"
						value={profile.preference2}
						onChange={handleChange}
						className="border rounded px-3 py-2"
					/>
				</label>

				<label className="flex flex-col gap-1">
					Birthday:
					<input
						type="text"
						name="preference3"
						value={profile.preference3}
						onChange={handleChange}
						className="border rounded px-3 py-2"
					/>
				</label>
				<div className="grid grid-cols-3 gap-4">
					<div>
				<label className="flex flex-col gap-1">
					Interest 1:
					<input
						type="text"
						name="interest1"
						value={profile.interest1}
						onChange={handleChange}
						className="border rounded px-3 py-2"
					/>
				</label>
					</div>
					<div>
				<label className="flex flex-col gap-1">
					Interest 2:
					<input
						type="text"
						name="interest2"
						value={profile.interest2}
						onChange={handleChange}
						className="border rounded px-3 py-2"
					/>
				</label>
				</div>
				<div>
				<label className="flex flex-col gap-1">
					Interest 3:
					<input
						type="text"
						name="interest3"
						value={profile.interest3}
						onChange={handleChange}
						className="border rounded px-3 py-2"
					/>
				</label>
				</div>
				</div>
				{/* <nav>
					<ul class = Focus time>
						<ul class="deroulant">
							<li>15 minutes</li>
							<li>30 mintes</li>
							<li>1hour</li>
							<li>all day</li>
						</ul> */}
				<label className="flex flex-col gap-1">
					Focus time:
					<input
						type="text"
						name="focusTime"
						value={profile.focusTime}
						onChange={handleChange}
						className="border rounded px-3 py-2"
					/>
				</label>
				<label className="flex flex-col gap-1">
					Password:
					<input
						type="password"
						name="password"
						value={profile.password}
						onChange={handleChange}
						className="border rounded px-3 py-2"
					/>
				</label>
				<label className="flex flex-col gap-1">
					Confirm password:
					<input
						type="password"
						name="confirmPassword"
						value={profile.confirmPassword}
						onChange={handleChange}
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
					className="bg-primary text-white rounded px-4 py-2 self-start"
				>
					Back
				</Link>

				{saved && <p className="text-green-600">Profile Saved</p>}
			</form>
		</main>
	);
}
