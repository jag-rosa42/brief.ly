import { useNavigate } from "react-router-dom";
import { useAuth } from "@/app/useAuth";
import { usePreferences } from "@/app/usePreferences";
import { useEffect, useState } from "react";
import type { SubmitEvent } from "react";
import { Link } from "@/shared/components/Link";

import { Division } from "@/shared/components/Division";
import { Form } from "@/shared/components/Form";
import { Text } from "@/shared/components/Text";
import { Input } from "@/shared/components/Input";
import { Button } from "@/shared/components/Button";
import { FilterChip } from "@/shared/components/FilterChip";
import type { FilterChipOption } from "@/shared/components/FilterChip";
import { Spinner } from "@/shared/components/Spinner";
import { ApiError } from "@/shared/components/api/client";
import { useProfile } from "@/features/profile/hooks/useProfile";
import type { Profile, ProfileUpdate, Topic } from "@/features/profile/types";

const MIN_INTERESTS = 1;
const MAX_INTERESTS = 4;

function validateUsername(value: string): string | null {
	const name = value.trim();
	if (name.length < 2) return `Username must be at least 2 characters.`;
	if (name.length > 14) return `Username must be at most 14 characters.`;
	return null;
}

// Topic ids are lowercase words ("technology"): shown with a capital letter.
function topicLabel(topicId: string): string {
	return topicId.charAt(0).toUpperCase() + topicId.slice(1);
}

function toOption(topic: Topic): FilterChipOption {
	return { value: topic.id, label: topicLabel(topic.id) };
}

function sameTopics(a: string[], b: string[]): boolean {
	return a.length === b.length && a.every((id) => b.includes(id));
}

type FieldName = "Name" | "interests";

type FormErrors = Partial<Record<FieldName | "form", string>>;

// 422 details name the field ("name", "topic_ids" or "topic_ids.0"):
// each message goes under its field, the others above the Save button.
function toFormErrors(err: unknown): FormErrors {
	if (!(err instanceof ApiError)) {
		return { form: "The profile could not be saved, please try again." };
	}
	if (err.code !== "VALIDATION_ERROR" || err.details.length === 0) {
		return { form: err.message || "The profile could not be saved, please try again." };
	}

	const next: FormErrors = {};
	for (const detail of err.details) {
		if (detail.field === "name") next.Name = detail.message;
		else if (detail.field.startsWith("topic_ids")) next.interests = detail.message;
		else next.form = detail.message;
	}
	return next;
}

interface ProfileFormProps {
	profile: Profile | null;
	topics: Topic[];
	save: (update: ProfileUpdate) => Promise<Profile>;
}

function ProfileForm({ profile, topics, save }: ProfileFormProps) {
	const [Name, setName] = useState(profile?.name ?? "");
	const [errors, setErrors] = useState<FormErrors>({});
	const [selectedInterests, setSelectedInterests] = useState<string[]>(profile?.topic_ids ?? []);
	const [saved, setSaved] = useState(false);
	const [isSaving, setIsSaving] = useState(false);

	const navigate = useNavigate();
	const { profileComplete, completeProfile } = useAuth();
	// TODO: remove with PreferencesContext once the Brief page reads Morning Briefing (#189).
	const { updatePreferences } = usePreferences();
	const limitReached = selectedInterests.length >= MAX_INTERESTS;

	function clearError(field: FieldName) {
		setErrors((prev) => ({ ...prev, [field]: undefined, form: undefined }));
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
		else {
			const nameError = validateUsername(Name);
			if (nameError) next.Name = nameError;
		}
		if (selectedInterests.length < MIN_INTERESTS) {
			next.interests = "Please select at least one interest";
		}
		setErrors(next);
		return Object.keys(next).length === 0;
	}

	// First save: both fields. After that, only what changed.
	function buildUpdate(): ProfileUpdate {
		const name = Name.trim();
		if (profile === null) return { name, topic_ids: selectedInterests };

		const update: ProfileUpdate = {};
		if (name !== profile.name) update.name = name;
		if (!sameTopics(selectedInterests, profile.topic_ids)) update.topic_ids = selectedInterests;
		return update;
	}

	async function handleSave(e: SubmitEvent) {
		e.preventDefault();
		setSaved(false);

		if (!validate()) return;

		const update = buildUpdate();
		// Nothing changed: the API refuses an empty update.
		if (Object.keys(update).length === 0) {
			setSaved(true);
			return;
		}

		setIsSaving(true);
		try {
			const savedProfile = await save(update);
			updatePreferences(savedProfile.topic_ids);
			setSaved(true);
			if (!profileComplete) {
				completeProfile();
				void navigate("/dashboard/brief");
			}
		} catch (err) {
			setErrors(toFormErrors(err));
		} finally {
			setIsSaving(false);
		}
	}

	return (
		<Form
			onSubmit={(e) => {
				void handleSave(e);
			}}
			actions={
				<div className="flex flex-col gap-3 w-full">
					{errors.interests && (
						<Text variant="error" role="alert">
							{errors.interests}
						</Text>
					)}
					{errors.form && (
						<Text variant="error" role="alert">
							{errors.form}
						</Text>
					)}
					{saved && <Text variant="success">Profile saved</Text>}
					<Button type="submit" variant="secondary" className="w-full" disabled={isSaving}>
						{isSaving ? "Saving..." : "Save"}
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
					setSaved(false);
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
					{topics.map(toOption).map((opt) => {
						const isSelected = selectedInterests.includes(opt.value);
						return (
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
	);
}

export function ProfilePage() {
	const { profile, topics, isLoading, error, save } = useProfile();
	const { profileComplete, completeProfile } = useAuth();

	// A user who already has a profile has finished the onboarding,
	// even if this browser does not know it yet.
	useEffect(() => {
		if (profile !== null && !profileComplete) completeProfile();
	}, [profile, profileComplete, completeProfile]);

	let content;
	if (isLoading) {
		content = <Spinner />;
	} else if (error) {
		content = (
			<Text variant="body" role="alert">
				{error}
			</Text>
		);
	} else {
		content = <ProfileForm profile={profile} topics={topics} save={save} />;
	}

	return (
		<Division variant="dashboardpage" className="items-center">
			<Text variant="title" className="mb-10 text-center">
				Profile
			</Text>
			<div className="w-full max-w-sm">
				<Text variant="subheading" className="mb-4">
					Personalise your brief
				</Text>
				<Division variant="featurecard" className="shadow-sm">
					{content}
				</Division>
			</div>
		</Division>
	);
}
