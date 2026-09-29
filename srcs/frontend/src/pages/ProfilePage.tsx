import { useState } from "react";
import type { SubmitEvent } from "react";
import type { ChangeEvent } from "react";
import { Link } from "react-router-dom";

import { Form } from "@/shared/components/Form";
import { Text } from "@/shared/components/Text";
import { Input } from "@/shared/components/Input";
import { Dropdown } from "@/shared/components/Dropdown";
import { Button } from "@/shared/components/Button";
import type { DropdownOption } from "@/shared/components/Dropdown";

//TODO: API call to add, here mock for test
const InterestOptions: DropdownOption[] = [
	{value: "sport", label: "Sport"},
	{value: "finance", label: "Finance"},
	{value: "coding", label: "Coding"},
	{value: "music", label: "Music"},
];

function getAvailableInterestOptions(
	currentValue: string,
	otherValues: string[]
): DropdownOption[] {
	return InterestOptions.filter(
		(opt) => opt.value === currentValue || !otherValues.includes(opt.value));
}

const focusTimeOptions: DropdownOption[] = [
	{value: "15min", label: "15 minutes"},
	{value: "30min", label: "30 minutes"},
	{value: "1h", label: "1 hour"},
];

export function ProfilePage() {
	const [lastName, setLastName] = useState("");
	const [firstName, setFirstName] = useState("");
	const [email, setEmail] = useState("");
	const [birthday, setBirthday] = useState("");

	const [preference1, setPreference1] = useState("");
	const [preference2, setPreference2] = useState("");
	const [preference3, setPreference3] = useState("");

	const [focusTime, setFocusTime] = useState("");
	const [showPasswordFields, setShowPasswordFields] = useState(false);
	const [password, setPassword] = useState("");
	const [confirmPassword, setConfirmPassword] = useState("");
	const [passwordError, setPasswordError] = useState("");
	const [interestError, setInterestError] = useState("");

	const [saved, setSaved] = useState(false);
	
	//TODO: add a function UseEffect with API call and error handling
	function handleSave(e: SubmitEvent) {
		e.preventDefault();
		if (showPasswordFields && password !== confirmPassword)
			{
				setPasswordError("Passwords don't match");
				setSaved(false);
				return;
			}
			setPasswordError("");
			setInterestError("");

// TODO: add API call
setSaved(true);
}
return (
	<main className="max-w-2xl mx-auto px-6 py-16">
	<Text variant="title" className="mb-6">
	    Profile
	</Text>
			<Form title="" onSubmit={handleSave}>
				<Input
					variant="main"
					label="Last name"
					name="lastName"
					value={lastName}
					onChange={(e: ChangeEvent<HTMLInputElement>) => setLastName(e.target.value)}/>
				<Input
					variant="main"
					label="First name"
					name="firstName"
					value={firstName}
					onChange={(e: ChangeEvent<HTMLInputElement>) => setFirstName(e.target.value)}/>
				<Input
					variant="main"
					label="Email"
					name="email"
					type="email"
					value={email}
					onChange={(e: ChangeEvent<HTMLInputElement>) => setEmail(e.target.value)}/>
				<Input
					variant="main"
					label="Birthday"
					name="birthday"
					type="date"
					value={birthday}
					onChange={(e: ChangeEvent<HTMLInputElement>) => setBirthday(e.target.value)}/>
					<div className="grid grid-cols-3 gap-4">
						<Dropdown
						variant="main"
						label="Interest 1"
						name="interest1"
						options={getAvailableInterestOptions(preference1, [preference2, preference3])}
						value={preference1}
						onChange={(e: ChangeEvent<HTMLSelectElement>) => setPreference1(e.target.value)}/>
						<Dropdown
						variant="main"
						label="Interest 2"
						name="interest2"
						options={getAvailableInterestOptions(preference2, [preference1, preference3])}
						value={preference2}
						onChange={(e: ChangeEvent<HTMLSelectElement>) => setPreference2(e.target.value)}/>
						<Dropdown
						variant="main"
						label="Interest 3"
						name="interest3"
						options={getAvailableInterestOptions(preference3, [preference1, preference2])}
						value={preference3}
						onChange={(e: ChangeEvent<HTMLSelectElement>) => setPreference3(e.target.value)}/>
						</div>
						    {interestError && <p className="text-error text-sm">{interestError}</p>}
						<Dropdown
						variant="main"
						label="Focus time"
						name="focusTime"
						options={focusTimeOptions}
						value={focusTime}
						onChange={(e: ChangeEvent<HTMLSelectElement>) => setFocusTime(e.target.value)}/>
						{!showPasswordFields && (
							<Button
							type="button"
							variant="secondary"
							className="self-start"
							onClick={() => setShowPasswordFields(true)}>
								Change password
								</Button>
							)}
							{showPasswordFields && (
								<div className="flex flex-col gap-4 border-t pt-4">
									<Input
									variant="main"
									label="New password"
									name="password"
									type="password"
									value={password}
									onChange={(e: ChangeEvent<HTMLInputElement>) => setPassword(e.target.value)}/>
									<Input
									variant="main"
									label="Confirm new password"
									name="confirmPassword"
									type="password"
									value={confirmPassword}
									error={passwordError}
									onChange={(e: ChangeEvent<HTMLInputElement>) => setConfirmPassword(e.target.value)}/>
									<Button
									type="button"
									variant="secondary"
									className="self-start"
									onClick={() => {
										setShowPasswordFields(false);
										setPassword("");
										setConfirmPassword("");
										setPasswordError("");
										}}>
											Cancel password change
											</Button>
											</div>
										)}
										<Button type="submit" variant="secondary">
											Save
											</Button>
											<Link to="/">
											<Button type="button" variant="primary">
												Back
												</Button>
												</Link>
												{saved && <p className="text-green-600">Profile Saved</p>}
												</Form>
												</main>
)}