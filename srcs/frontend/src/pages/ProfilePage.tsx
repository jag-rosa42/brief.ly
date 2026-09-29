import { useState } from "react";
import type { SubmitEvent } from "react";
import { Link } from "@/shared/components/Link";

import { Division } from "@/shared/components/Division";
import { Form } from "@/shared/components/Form";
import { Text } from "@/shared/components/Text";
import { Input } from "@/shared/components/Input";
import { Button } from "@/shared/components/Button";
import { FilterChip } from "@/shared/components/FilterChip";
import type { FilterChipOption } from "@/shared/components/FilterChip";

const MIN_INTERESTS = 1;
const MAX_INTERESTS = 4;


//TODO: API call to add, here mock for test
const InterestOptions: FilterChipOption[] = [
	{value: "science", label: "Science"},
	{value: "business", label: "Business"},
	{value: "entertainment", label: "Entertainment"},
	{value: "general", label: "General"},
	{value: "health", label: "Health"},
	{value: "sport", label: "Sport"},
	{value: "technologies", label: "Technologies"},
];

type FieldName = 
	| "Name"
	| "interests";

type FormErrors = Partial<Record<FieldName, string>>;

export function ProfilePage() {
	const [Name, setName] = useState("");
	const [errors, setErrors] = useState<FormErrors>({});
	const[selectedInterests, setSelectedInterests] = useState<string[]>([]);
	const [saved, setSaved] = useState(false);

	const limitReached = selectedInterests.length >= MAX_INTERESTS;

	function clearError(field: FieldName) {
		setErrors((prev) => ({ ...prev, [field]: undefined}));
	}

	function toggleInterest(value: string) {
		setSaved(false);
		clearError("interests");
		if (selectedInterests.includes(value)) {
			setSelectedInterests(selectedInterests.filter((v) => v !== value));
		} else if (!limitReached) {
		setSelectedInterests([...selectedInterests, value]);
	}
}

	function validate(): boolean {
		const next: FormErrors = {};

		if (Name.trim() === "") next.Name = "Name is required";
		if (selectedInterests.length < MIN_INTERESTS) {
			next.interests = "Please select at least one interest";
		}
		setErrors(next);
		return(Object.keys(next).length === 0);
	}

	//TODO: add a function UseEffect with API call and error handling
	function handleSave(e: SubmitEvent) {
		e.preventDefault();
		setSaved(false);

		if (!validate())
			return;
		//TODO: add API call
		setSaved(true);
	}

return (
	<Division variant="page">
		<Text variant="title" className="mb-10 text-center">
			Profile
		</Text>
		<div className="w-full max-w-sm">
			<Text variant="subheading" className="mb-4">
				Edit your profile
			</Text>
			<Division variant="featurecard" className="shadow-sm">
				<Form
					onSubmit={handleSave}
					actions={
						<div className="flex flex-col gap-3 w-full">
							{errors.interests && (
								<Text variant="error" role="alert">
									{errors.interests}
								</Text>
							)}
							{saved && 
								<Text variant="success">
									Profile saved
								</Text>
							}
							<Button type="submit" variant="secondary" className ="w-full">
								Save
							</Button>
							<Link to="/" variant="primary" className="w-full text-center">
								Back
							</Link>
						</div>
					}
				>
					<Input
						variant="main"
						label="Name"
						value={Name}
						name="name"
						error={errors.Name}
						onChange={(e) => {
							setName(e.target.value);
							clearError("Name");
						}}
					/>
					<div className="flex flex-col gap-3">
						<div>
							<Text variant="body" className="font-semibold">
								Interests
							</Text>
							<Text variant="body" className="text-sm text-info">
								Pick between one and four interests
							</Text>
						</div>
						<div className="flex flex-wrap justify-center gap-2">
							{InterestOptions.map((opt) => {
								const isSelected = selectedInterests.includes(opt.value);
								return(
									<FilterChip
										key={opt.value}
										options={opt}
										selected={isSelected}
										disabled={!isSelected && limitReached}
										onToggle={toggleInterest}
									/>
								);
							})}
						</div>
					</div>
					</Form>
			</Division>
		</div>
	</Division>
	);
}