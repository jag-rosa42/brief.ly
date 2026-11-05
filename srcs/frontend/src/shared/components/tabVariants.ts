import type { ButtonVariant } from "@/shared/components/buttonVariants";

export const tabVariant = ["main", "sub", "pill", "side"] as const;
export type TabVariant = (typeof tabVariant)[number];

export function getTabStyle(style: TabVariant): string {
	switch (style) {
		case "main":
			return "flex gap-2 border-b border-secondary";
		case "sub":
			return "flex gap-1 bg-accent p-1 rounded";
		case "pill":
			return "inline-flex w-fit gap-1 rounded-full bg-background-light/50 p-1 backdrop-blur-sm";
		case "side":
			return "flex flex-col gap-2";
	}
}

export function getTabButtonVariant(isActive: boolean, variant: TabVariant): ButtonVariant {
	if (variant === "side") {
		if (isActive) {
			return "secondary";
		}
		return "primary";
	}
	return "simple";
}

export function getTabButtonStyle(isActive: boolean, variant: TabVariant): string {
	if (variant === "side") {
		return "disabled:opacity-50 disabled:cursor-not-allowed";
	}
	if (variant === "pill") {
		if (isActive)
			return "rounded-full bg-background-light px-4 py-1.5 text-sm font-semibold text-primary-dark shadow-sm";
		return "rounded-full px-4 py-1.5 text-sm text-info hover:text-accent";
	}
	if (isActive) return "px-4 py-2 border-b-2 border-primary font-bold text-primary";
	return "px-4 py-2 text-gray-500 hover:text-primary";
}
