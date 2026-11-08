import { useNavigate } from "react-router-dom";
import { useProfileForm } from "@/features/profile/useProfileForm";
import type React from "react";

import { Link } from "@/shared/components/Link";
import { Division } from "@/shared/components/Division";
import { Form } from "@/shared/components/Form";
import { Text } from "@/shared/components/Text";
import { Input } from "@/shared/components/Input";
import { Button } from "@/shared/components/Button";
import { FilterChip } from "@/shared/components/FilterChip";
import type { FilterChipOption } from "@/shared/components/FilterChip";
import { useProfile } from "@/app/useProfile";
import { topicLabel } from "@/shared/utils/article";

const MAX_INTERESTS = 4;

export function ProfilePage() {
	const navigate = useNavigate();
	const {
		mode,
		topics,
		name,
		setName,
		topicIds,
		toggleTopic,
		loading,
		loadError,
		reload,
		submitting,
		success,
		errors,
		submit,
		canSubmit,
	} = useProfileForm();
	const { isProfileComplete } = useProfile();

	// Transformation des topics du backend en options pour FilterChip
	const interestOptions: FilterChipOption[] = topics.map((topic) => ({
		value: topic.id,
		label: topicLabel(topic.id),
	}));

	async function handleSave(e: React.SubmitEvent<HTMLFormElement>) {
		e.preventDefault();
		const wasCreate = mode === "create"; // capturé AVANT le submit
		const saved = await submit();

		if (saved !== null) {
			if (wasCreate) {
				void navigate("/dashboard/brief");
			}
		}
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
					<Form
						onSubmit={(e) => {
							void handleSave(e);
						}}
						actions={
							<div className="flex flex-col gap-3 w-full">
								{errors.topics && (
									<Text variant="error" role="alert">
										{errors.topics}
									</Text>
								)}
								{errors.form && (
									<Text variant="error" role="alert">
										{errors.form}
									</Text>
								)}
								{success && <Text variant="success">Profile saved</Text>}
								<Button type="submit" variant="secondary" className="w-full" disabled={!canSubmit}>
									{submitting ? "Saving..." : "Save"}
								</Button>
								<Link
									to={isProfileComplete ? "/dashboard/brief" : "/"}
									variant="primary"
									className="w-full text-center"
								>
									Back
								</Link>
							</div>
						}
					>
						<Input
							variant="main"
							label="Name"
							value={name}
							name="name"
							error={errors.name}
							onChange={(e) => setName(e.target.value)}
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

							{loading && <Text variant="body">Loading interests...</Text>}

							{!loading && loadError && (
								<div className="flex flex-col items-center gap-2">
									<Text variant="error" role="alert">
										{loadError}
									</Text>
									<Button type="button" variant="secondary" onClick={() => void reload()}>
										Retry
									</Button>
								</div>
							)}

							{!loading && !loadError && (
								<div className="flex flex-wrap justify-center gap-2">
									{interestOptions.map((opt) => {
										const isSelected = topicIds.includes(opt.value);
										return (
											<FilterChip
												key={opt.value}
												options={opt}
												selected={isSelected}
												disabled={!isSelected && topicIds.length >= MAX_INTERESTS}
												onToggle={toggleTopic}
											/>
										);
									})}
								</div>
							)}
						</div>
					</Form>
				</Division>
			</div>
		</Division>
	);
}
