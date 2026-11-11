// The drawing of each icon (an SVG path on a 24 × 24 grid), used by Icon.tsx.

export const ICON_PATHS = {
	close: "M6 6l12 12M18 6L6 18",
	"arrow-left": "M19 12H5M11 6l-6 6 6 6",
	"arrow-right": "M5 12h14M13 6l6 6-6 6",
	check: "M5 12.5l4.5 4.5L19 7",
	bookmark: "M7 4h10v16l-5-4-5 4z",
	search: "M10.5 17a6.5 6.5 0 1 0 0-13 6.5 6.5 0 0 0 0 13zM20 20l-4.8-4.8",
} as const;

export type IconName = keyof typeof ICON_PATHS;

export const ICON_NAMES = Object.keys(ICON_PATHS) as IconName[];
