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
	const [birthday, setBirthday] = useState("");
	const [displayName, setDisplayName] = useState("");
	const [lastNameError, setLastNameError] = useState("");
	const [firstNameError, setFirstNameError] = useState("");
	const [displayNameError, setDisplayNameError] = useState("");
	const [birthdayError, setBirthdayError] = useState("");

	const [preference1, setPreference1] = useState("");
	const [preference2, setPreference2] = useState("");
	const [preference3, setPreference3] = useState("");

	const [focusTime, setFocusTime] = useState("");
	const [showPasswordFields, setShowPasswordFields] = useState(false);
	const [password, setPassword] = useState("");
	const [confirmPassword, setConfirmPassword] = useState("");
	const [passwordError, setPasswordError] = useState("");
	const [preferenceError, setPreferenceError] = useState("");
	const [focusTimeError, setFocusTimeError] = useState("");

	const [saved, setSaved] = useState(false);
	
	//TODO: add a function UseEffect with API call and error handling
	function handleSave(e: SubmitEvent) {
		e.preventDefault();
		setSaved(false);
		setLastNameError("");
		setFirstNameError("");
		setDisplayNameError("");
		setBirthdayError("");
		setPreferenceError("");
		setFocusTimeError("");

		let hasError = false;
    	
    if (lastName.trim() === "") {
        setLastNameError("Last name is required");
        hasError=true;
    }
	    if (firstName.trim() === "") {
        setFirstNameError("First name is required");
        hasError=true;
    }
	    if (displayName.trim() === "") {
        setDisplayNameError("Display name is required");
        hasError=true;
    }
	    if (birthday.trim() === "") {
        setBirthdayError("Birthday is required");
        hasError=true;
    }
	if (preference1 === "" || preference2 === "" || preference3 === "") {
    setPreferenceError("Please select all three interests");
    hasError = true;
}

if (focusTime === "") {
    setFocusTimeError("Please select a focus time");
    hasError = true;
}

		if (showPasswordFields && password !== confirmPassword)
			{
				setPasswordError("Passwords don't match");
				setSaved(false);
				return;
			}
			setPasswordError("");
		if(hasError)
	{
		return;
	}
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
					error={lastNameError}
					onChange={(e: ChangeEvent<HTMLInputElement>) => {
						setLastName(e.target.value);
						setLastNameError("");
					}}/>
				<Input
					variant="main"
					label="First name"
					name="firstName"
					value={firstName}
					error={firstNameError}
					onChange={(e: ChangeEvent<HTMLInputElement>) => {
						setFirstName(e.target.value);
						setFirstNameError("");
					}}/>
				<Input
					variant="main"
					label="Display name"
					name="displayName"
					value={displayName}
					error={displayNameError}
					onChange={(e: ChangeEvent<HTMLInputElement>) =>
						{setDisplayName(e.target.value);
						setDisplayNameError("");
						}}/>
				<Input
					variant="main"
					label="Birthday"
					name="birthday"
					type="date"
					value={birthday}
					error={birthdayError}
					onChange={(e: ChangeEvent<HTMLInputElement>) => {
						setBirthday(e.target.value);
						setBirthdayError("");
					}}/>
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
						    {preferenceError && <p className="text-error text-sm">{preferenceError}</p>}
						<Dropdown
						variant="main"
						label="Focus time"
						name="focusTime"
						options={focusTimeOptions}
						value={focusTime}
						onChange={(e: ChangeEvent<HTMLSelectElement>) => {
							setFocusTime(e.target.value)
							setFocusTimeError("")}}/>
						{focusTimeError && (<p className="text-error text-sm">{focusTimeError}</p>)}
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
												{saved && <p className="text-success">Profile Saved</p>}
												</Form>
												</main>
)}