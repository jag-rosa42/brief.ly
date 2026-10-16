import type { ChangeEvent } from "react";

import { getDropdownStyle, type DropdownOption, type DropdownVariant, } from "./dropdownVariants";

export interface DropdownFieldProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
	label?: string;
	error?: string;
	info?: string;
	variant: DropdownVariant;
	onChange: (e: ChangeEvent<HTMLSelectElement>) => void;
	options: DropdownOption[];
	placeholder?: string;
}

export function Dropdown({
	label,
	error,
	info,
	variant,
	options,
	placeholder = "Select...",
	className = "",
	id,
	...props
}:DropdownFieldProps) {
	const style = getDropdownStyle(variant);
	const dropdownId = id ?? props.name;
	return (
		<label htmlFor={dropdownId} className="flex flex-col gap-1">
			{label}
		<select
			id={dropdownId}
			{...props}
			className={`${style} ${className}`}
			>
				<option value="" disabled>
					{placeholder}
				</option>
				{options.map((opt) => (
					<option key={opt.value} value={opt.value}>
						{opt.label}
					</option>
				))}
			</select>
			{error && <span className="text-sm text-error">{error}</span>}
			{info && <span className="text-sm text-info">{info}</span>}
			</label>
	);
}