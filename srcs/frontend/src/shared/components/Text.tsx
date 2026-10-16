import { getTextStyle, getTextTag, type TextVariant } from "@/shared/components/textVariants";


interface TextProps extends React.HTMLAttributes<HTMLElement>
{
	variant: TextVariant;
}

export function Text({
	variant,
	children,
	className,
	...props
}: TextProps) {
	const style = getTextStyle(variant);
	const combinedClassName = `${style} ${className ?? ""}`;

	switch (getTextTag(variant)) {
		case "h1":
			return <h1 {...props} className={combinedClassName}>{children}</h1>;
		case "h2":
			return <h2 {...props} className={combinedClassName}>{children}</h2>;
		case "h3":
			return <h3 {...props} className={combinedClassName}>{children}</h3>;
		default:
			return <p {...props} className={combinedClassName}>{children}</p>;
	}
}
