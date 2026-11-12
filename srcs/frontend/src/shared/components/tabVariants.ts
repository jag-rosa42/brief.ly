import {
	composeSurfaceVariant,
	getNeomorphicVariant,
	type Appearance,
	type SurfaceVariant,
} from "@/shared/components/neomorphicVariants";
import type { ButtonVariant } from "@/shared/components/buttonVariants";

export const tabVariant = ["main", "sub", "pill", "side"] as const;
export type TabVariant = (typeof tabVariant)[number];

const pillGroup: SurfaceVariant = {
	layout: "inline-flex w-fit gap-1 rounded-full p-1",
	surface: "bg-background-light/50",
	decoration: "backdrop-blur-sm",
};

const selectedPill: SurfaceVariant = {
	layout: "rounded-full px-4 py-1.5 text-sm font-semibold text-primary-dark",
	surface: "bg-background-light",
	decoration: "shadow-sm",
};

export function getTabStyle(style: TabVariant, appearance: Appearance = "classic"): string {
	switch (style) {
		case "main":
			return "flex gap-2 border-b border-secondary";
		case "sub":
			return "flex gap-1 bg-accent p-1 rounded";
		case "pill":
			return composeSurfaceVariant(
				pillGroup,
				appearance === "neomorphic" ? getNeomorphicVariant("up") : {},
			);
		case "side":
			return "flex flex-col gap-3";
	}
}

export function getTabButtonVariant(variant: TabVariant): ButtonVariant {
	if (variant === "side") {
		return "side";
	}
	return "simple";
}

export function getTabButtonStyle(
	isActive: boolean,
	variant: TabVariant,
	appearance: Appearance = "classic",
): string {
	if (variant === "side") {
		return "text-left disabled:opacity-50 disabled:cursor-not-allowed";
	}
	if (variant === "pill") {
		if (isActive)
			return composeSurfaceVariant(
				selectedPill,
				appearance === "neomorphic" ? getNeomorphicVariant("down") : {},
			);
		return "rounded-full px-4 py-1.5 text-sm text-info hover:text-accent";
	}
	if (isActive) return "px-4 py-2 border-b-2 border-primary font-bold text-primary";
	return "px-4 py-2 text-gray-500 hover:text-primary";
}
