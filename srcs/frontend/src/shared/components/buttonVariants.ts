export const buttonVariants = [
	"primary",
	"side",
	"secondary",
	"simple",
	"title",
	"main",
	"link",
	"chip",
] as const;
export type ButtonVariant = (typeof buttonVariants)[number];

const outlinedButtonBase =
	"[--relief-surface:var(--color-background)] text-primary px-4 py-2 rounded-[999px] hover:text-primary-dark";

export function getButtonStyle(style: ButtonVariant, selected = false): string {
	switch (style) {
		case "primary":
			return `${outlinedButtonBase} border-1 border-primary hover:border-primary-dark`;
		case "side":
			return outlinedButtonBase;
		case "secondary":
			return "bg-primary [--relief-surface:var(--color-primary)] hover:[--relief-surface:var(--color-primary-dark)] text-background px-4 py-2 rounded-[999px] \
				hover:bg-primary-dark";
		case "simple":
			return "[--relief-surface:var(--color-background)] font-serif text-accent-dark";
		case "title":
			return "[--relief-surface:var(--color-background)] font-bold text-xl text-primary";
		case "main":
			return "bg-accent-dark [--relief-surface:var(--color-accent-dark)] hover:[--relief-surface:var(--color-accent)] text-background px-5 py-2.5 rounded-[999px] hover:bg-accent";
		case "link":
			return "inline-flex items-center gap-2 bg-primary [--relief-surface:var(--color-primary)] hover:[--relief-surface:var(--color-primary-dark)] text-background px-4 py-2 rounded-[999px] hover:bg-primary-dark";
		case "chip":
			return selected
				? "rounded-full border px-4 py-1.5 text-sm font-semibold transition-colors border-primary bg-primary [--relief-surface:var(--color-primary)] text-white"
				: "rounded-full border px-4 py-1.5 text-sm font-semibold transition-colors border bg-white [--relief-surface:white] text-accent hover:border-primary";
	}
}
