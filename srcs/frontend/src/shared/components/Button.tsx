import { getButtonStyle, type ButtonVariant } from "@/shared/components/buttonVariants";

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
	variant: ButtonVariant;
	selected?: boolean;
}

export function Button({ variant, children, className, selected, ...props }: ButtonProps) {
	const style = getButtonStyle(variant, selected);

	return (
		<button {...props} className={`${style} ${className ?? ""}`}>
			{children}
		</button>
	);
}
