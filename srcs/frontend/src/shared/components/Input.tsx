import type { ChangeEvent } from "react";

export const InputVariant = ["main", "sub"] as const;
export type InputVariant = typeof InputVariant[number];

export interface InputFieldProps extends React.InputHTMLAttributes<HTMLInputElement> {
	label?: string;
	error?: string;
	info?: string;
	variant: InputVariant;
	onChange: (e: ChangeEvent<HTMLInputElement>) => void;
}

export function getInputStyle(variant:InputVariant): string
{
	switch(variant) {
		case "main":
			return("border rounded px-4 py-3");
		case "sub":
			return("border rounded px-3 py-2");
	}
}

export function Input({
	label,
	error,
	info,
	variant,
	className = "",
	id,
	...props
}:InputFieldProps) {
	const style = getInputStyle(variant);
	const inputId = id ?? props.name;

	return (
		<label htmlFor={inputId} className="flex flex-col gap-1">
			{label}
			<input
				id={inputId}
				{...props}
				className={`${style} ${className}`}>
			</input>
			{error && <span className="text-sm text-error">{error}</span>}
			{info && <span className="text-sm text-info">{info}</span>}
		</label>
	);
}