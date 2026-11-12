import {
	getDivStyle,
	type DivShadow,
	type DivVariant,
	type SurfaceDivVariant,
} from "@/shared/components/divVariants";
import type { Relief } from "@/shared/components/neomorphicVariants";

type SurfaceProps =
	| { variant: SurfaceDivVariant; appearance?: "classic"; shadow?: DivShadow; relief?: never }
	| { variant: SurfaceDivVariant; appearance: "neomorphic"; relief?: Relief; shadow?: never };

interface LayoutProps {
	variant: Exclude<DivVariant, SurfaceDivVariant>;
	appearance?: never;
	relief?: never;
	shadow?: never;
}

type DivProps = React.HTMLAttributes<HTMLDivElement> & (SurfaceProps | LayoutProps);

export function Division({
	variant,
	appearance = "classic",
	relief = "up",
	shadow,
	children,
	className,
	...props
}: DivProps) {
	const divVariant = getDivStyle(
		variant,
		appearance,
		shadow ?? (variant === "dashboardcard" ? "soft" : "none"),
		relief,
	);

	return (
		<div {...props} className={`${divVariant} ${className ?? ""}`}>
			{children}
		</div>
	);
}
