import { getDivStyle, type DivVariant } from "@/shared/components/divVariants";

interface DivProps extends React.HTMLAttributes<HTMLDivElement> {
	variant: DivVariant;
}

export function Division({ variant, children, className, ...props }: DivProps) {
	const divVariant = getDivStyle(variant);

	return (
		<div {...props} className={`${divVariant} ${className ?? ""}`}>
			{children}
		</div>
	);
}
