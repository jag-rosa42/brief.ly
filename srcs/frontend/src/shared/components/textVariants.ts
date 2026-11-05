export const textVariants = [
	"title",
	"heading",
	"subheading",
	"body",
	"lead",
	"label",
	"error",
	"success",
] as const;
export type TextVariant = (typeof textVariants)[number];

export type TextTag = "h1" | "h2" | "h3" | "p";

export function getTextStyle(style: TextVariant): string {
	switch (style) {
		case "title":
			return "font-serif text-4xl font-bold text-primary";
		case "heading":
			return "font-sans font-semibold text-xl text-accent-dark";
		case "subheading":
			return "font-sans font-semibold text-2xl text-secondary";
		case "body":
			return "text-accent leading-relaxed";
		case "lead":
			return "font-serif text-lg md:text-xl text-accent-dark";
		case "label":
			return "text-[11px] font-semibold uppercase tracking-wider";
		case "error":
			return "text-error";
		case "success":
			return "text-success";
	}
}

export function getTextTag(style: TextVariant): TextTag {
	switch (style) {
		case "title":
			return "h1";
		case "heading":
			return "h2";
		case "subheading":
			return "h2";
		default:
			return "p";
	}
}
