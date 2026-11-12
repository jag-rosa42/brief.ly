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
			return "inline-flex w-fit max-w-full overflow-x-auto gap-1 rounded-full bg-background-light/50 p-1 backdrop-blur-sm";
		case "side":
			return "flex gap-2 overflow-x-auto md:flex-col md:overflow-visible";
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
		// shrink-0 + whitespace-nowrap: in the mobile row, a tab keeps its label
		// on one line; the row scrolls instead.
		return "shrink-0 whitespace-nowrap disabled:opacity-50 disabled:cursor-not-allowed";
	}
	if (variant === "pill") {
		if (isActive)
			return "shrink-0 whitespace-nowrap rounded-full bg-background-light px-4 py-1.5 text-sm font-semibold text-primary-dark shadow-sm";
		return "shrink-0 whitespace-nowrap rounded-full px-4 py-1.5 text-sm text-info hover:text-accent";
	}
	if (isActive) return "px-4 py-2 border-b-2 border-primary font-bold text-primary";
	return "px-4 py-2 text-gray-500 hover:text-primary";
}
