import React from "react";
import { Division } from "@/shared/components/Division";
import { Text } from "@/shared/components/Text";
import type { Appearance } from "@/shared/components/neomorphicVariants";

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
	title?: string;
	description?: string;
	children?: React.ReactNode;
	className?: string;
	appearance?: Appearance;
}

export function Card({
	title,
	description,
	children,
	className,
	appearance = "classic",
	...props
}: CardProps) {
	const surfaceProps =
		appearance === "neomorphic"
			? ({ appearance, relief: "up" } as const)
			: ({ appearance, shadow: "sm-hover-md" } as const);
	return (
		<Division variant="featurecard" {...surfaceProps} className={className} {...props}>
			{title && <Text variant="subheading"> {title}</Text>}
			{description && <Text variant="body">{description}</Text>}
			{children}
		</Division>
	);
}
