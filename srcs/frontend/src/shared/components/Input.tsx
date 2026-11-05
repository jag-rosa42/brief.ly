import type { ChangeEvent } from "react";
import { getInputStyle, type InputVariant } from "@/shared/components/inputVariants";

export interface InputFieldProps extends React.InputHTMLAttributes<HTMLInputElement> {
	label?: string;
	error?: string;
	info?: string;
	variant: InputVariant;
	onChange: (e: ChangeEvent<HTMLInputElement>) => void;
}

export function Input({
	label,
	error,
	info,
	variant,
	className = "",
	id,
	...props
}: InputFieldProps) {
	const style = getInputStyle(variant);
	const inputId = id ?? props.name;

	return (
		<label htmlFor={inputId} className="flex flex-col gap-1">
			{label}
			<input id={inputId} {...props} className={`${style} ${className}`} />
			{error && (
				<span role="alert" className="text-sm text-error">
					{error}
				</span>
			)}
			{info && <span className="text-sm text-info">{info}</span>}
		</label>
	);
}
