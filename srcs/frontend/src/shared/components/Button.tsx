import { getButtonStyle, type ButtonVariant } from "@/shared/components/buttonVariants";
import { getNeomorphicStyle, type Relief } from "@/shared/components/neomorphicVariants";

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
	variant: ButtonVariant;
	selected?: boolean;
	relief?: Relief;
}

export function Button({
	variant,
	children,
	className,
	selected,
	relief = "none",
	...props
}: ButtonProps) {
	const style = getButtonStyle(variant, selected);

	return (
		<button {...props} className={`${style} ${getNeomorphicStyle(relief)} ${className ?? ""}`}>
			{children}
		</button>
	);
}
