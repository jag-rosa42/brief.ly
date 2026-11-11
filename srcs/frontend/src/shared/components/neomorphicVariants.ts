export const appearances = ["classic", "neomorphic"] as const;
export type Appearance = (typeof appearances)[number];
export const reliefs = ["up", "down", "none"] as const;
export type Relief = (typeof reliefs)[number];

export interface SurfaceVariant {
	layout: string;
	surface: string;
	decoration?: string;
}

export function composeSurfaceVariant(
	base: SurfaceVariant,
	overrides: Partial<SurfaceVariant> = {},
): string {
	const style = { ...base, ...overrides };
	return [style.layout, style.surface, style.decoration].filter(Boolean).join(" ");
}

export function getNeomorphicVariant(relief: Relief): Partial<SurfaceVariant> {
	return {
		surface: "bg-background [--relief-surface:var(--color-background)]",
		decoration: getNeomorphicStyle(relief),
	};
}

export function getNeomorphicStyle(relief: Relief = "none"): string {
	switch (relief) {
		case "up":
			return "shadow-relief-up";
		case "down":
			return "shadow-relief-down";
		case "none":
			return "";
	}
}
