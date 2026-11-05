import React from "react";
import { Division } from "@/shared/components/Division";
import { Text } from "@/shared/components/Text";

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
	title?: string;
	description?: string;
	children?: React.ReactNode;
	className?: string;
}

export function Card({ title, description, children, className, ...props }: CardProps) {
	return (
		<Division
			variant="featurecard"
			className={`shadow-sm hover:shadow-md transition-shadow ${className ?? ""}`}
			{...props}
		>
			{title && <Text variant="subheading"> {title}</Text>}
			{description && <Text variant="body">{description}</Text>}
			{children}
		</Division>
	);
}
