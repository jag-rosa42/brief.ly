import { Button } from "@/shared/components/Button";

export interface FilterChipOption {
	value: string;
	label: string;
	description?: string;
}

export interface FilterChipProps {
	selected: boolean;
	disabled?: boolean;
	className?: string;
	onToggle: (value: string) => void;
	options: FilterChipOption;
}

export function FilterChip({
	selected,
	disabled,
	className = "",
	onToggle,
	options,
}: FilterChipProps) {
	return (
		<Button
			type="button"
			variant="chip"
			onClick={() => onToggle(options.value)}
			selected={selected}
			aria-pressed={selected}
			disabled={disabled}
			className={`rounded-full border px-4 py-1.5 text-sm font-semibold transition-colors
				${selected ? "border-primary bg-primary text-white" : "border bg-white text-accent hover:border-primary"}
				${disabled ? "cursor-not-allowed opacity-50" : "cursor-pointer"}
				${className}
			`}
		>
			{options.label}
		</Button>
	);
}
