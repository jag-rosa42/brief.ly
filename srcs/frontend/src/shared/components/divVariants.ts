import {
	composeSurfaceVariant,
	getNeomorphicVariant,
	type Appearance,
	type Relief,
	type SurfaceVariant,
} from "@/shared/components/neomorphicVariants";

export const divVariants = [
	"featurecard",
	"content",
	"page",
	"dashboardcard",
	"stack",
	"dashboardpage",
] as const;
export type DivVariant = (typeof divVariants)[number];
export type SurfaceDivVariant = Extract<DivVariant, "featurecard" | "dashboardcard">;
export const divShadows = ["none", "sm", "soft", "sm-hover-md", "sm-hover-soft"] as const;
export type DivShadow = (typeof divShadows)[number];

export function getDivShadowStyle(shadow: DivShadow): string {
	switch (shadow) {
		case "none":
			return "";
		case "sm":
			return "shadow-sm";
		case "soft":
			return "shadow-soft";
		case "sm-hover-md":
			return "shadow-sm hover:shadow-md transition-shadow";
		case "sm-hover-soft":
			return "shadow-sm hover:shadow-soft-hover transition-shadow";
	}
}

const featureCard: SurfaceVariant = {
	layout: "rounded-xl p-6 flex flex-col gap-y-3",
	surface: "bg-white [--relief-surface:white]",
	decoration: "border border",
};

const dashboardCard: SurfaceVariant = {
	layout: "rounded-3xl p-6 flex flex-col gap-y-3",
	surface: "bg-white/60 [--relief-surface:color-mix(in_srgb,white_60%,var(--color-background))]",
	decoration: "border border-white/70 backdrop-blur-sm",
};

function getCardStyle(
	base: SurfaceVariant,
	appearance: Appearance,
	shadow: DivShadow,
	relief: Relief,
): string {
	if (appearance === "neomorphic") {
		return composeSurfaceVariant(base, getNeomorphicVariant(relief));
	}
	return composeSurfaceVariant(base, {
		decoration: [base.decoration, getDivShadowStyle(shadow)].filter(Boolean).join(" "),
	});
}

export function getDivStyle(
	style: DivVariant,
	appearance: Appearance = "classic",
	shadow: DivShadow = "none",
	relief: Relief = "up",
): string {
	switch (style) {
		case "featurecard":
			return getCardStyle(featureCard, appearance, shadow, relief);
		case "content":
			return `text-accent leading-relaxed ${getDivShadowStyle(shadow)}`;
		case "page":
			return `bg-background flex flex-col items-center pt-12 px-4 ${getDivShadowStyle(shadow)}`;
		case "dashboardcard":
			return getCardStyle(dashboardCard, appearance, shadow, relief);
		case "stack":
			return `flex flex-col gap-2 ${getDivShadowStyle(shadow)}`;
		case "dashboardpage":
			return `flex flex-col mx-auto w-full p-6 ${getDivShadowStyle(shadow)}`;
	}
}
