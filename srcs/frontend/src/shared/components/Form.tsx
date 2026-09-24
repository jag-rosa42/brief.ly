import type { SubmitEvent } from "react";
import { Text } from "@/shared/components/Text";

interface FormProps {
	title?: string;
	onSubmit?: (e: SubmitEvent<HTMLFormElement>) => void;
	children: React.ReactNode;
	actions?: React.ReactNode;
}

export function Form({title, onSubmit, children, actions }: FormProps) {
	return (
		<form className="flex flex-col gap-4" onSubmit={onSubmit}>
			{title && <Text variant="heading">{title}</Text>}
			{children}
			<div className="flex gap-2">{actions}</div>
		</form>
	);
}