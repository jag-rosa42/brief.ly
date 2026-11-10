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
			return "flex w-full gap-1 overflow-x-auto rounded-full bg-[#f1e8dc] p-2 shadow-[inset_5px_5px_10px_#c7b8a78c,inset_-5px_-5px_10px_#fff9f0c7]";
		case "side":
			return "flex gap-2 overflow-x-auto md:flex-col";
	}
}

export function getTabButtonVariant(_isActive: boolean, variant: TabVariant): ButtonVariant {
	if (variant === "side") {
		return "simple";
	}
	return "simple";
}

export function getTabButtonStyle(isActive: boolean, variant: TabVariant): string {
	if (variant === "side") {
		return `flex min-h-12 min-w-max items-center gap-3 rounded-2xl border-0 px-4 py-3 text-left font-sans! text-sm font-semibold shadow-none before:text-xl before:text-primary before:content-['◌'] hover:bg-[#f7f0e7] disabled:cursor-not-allowed disabled:opacity-50 md:w-full md:text-base ${isActive ? "bg-[#f1e8dc] text-accent! shadow-[inset_5px_5px_10px_#c7b8a78c,inset_-5px_-5px_10px_#fff9f0c7]" : "bg-transparent text-[#7b6b62]!"}`;
	}
	if (variant === "pill") {
		if (isActive)
			return "min-w-max flex-1 rounded-full bg-[#f1e8dc] px-4 py-3 font-sans text-sm font-semibold text-primary shadow-[5px_6px_12px_#c5b6a570,-5px_-5px_12px_#fff9f0]";
		return "min-w-max flex-1 rounded-full px-4 py-3 font-sans text-sm font-medium text-[#7b6b62] hover:text-accent";
	}
	if (isActive) return "px-4 py-2 border-b-2 border-primary font-bold text-primary";
	return "px-4 py-2 text-gray-500 hover:text-primary";
}
