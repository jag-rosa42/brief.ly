import type { SVGProps } from "react";
import { ICON_PATHS, type IconName } from "@/shared/components/iconPaths";

// The app's icons, drawn for Brief.ly on one 24 × 24 grid with the same
// 2 px rounded stroke, so they all look alike. They are SVG, not text
// characters: a character like "🡪" depends on the fonts of the user's system
// and can show as an empty box.
//
// The stroke uses currentColor: an icon takes the color of the text around it
// (hover, disabled...), with no color of its own.

const SIZES = {
	sm: "size-4",
	md: "size-5",
	lg: "size-6",
} as const;

export type IconSize = keyof typeof SIZES;

// Every native <svg> attribute is accepted too (data-*, aria-describedby...)
// and passed on to the <svg>.
interface IconProps extends Omit<SVGProps<SVGSVGElement>, "name" | "children"> {
	name: IconName;
	size?: IconSize;
	// Only for an icon that stands alone and means something (no text next
	// to it). Next to a text, or in a button that has an aria-label, leave it
	// out: the icon is then hidden from screen readers.
	label?: string;
}

export function Icon({ name, size = "md", label, className = "", ...props }: IconProps) {
	return (
		<svg
			viewBox="0 0 24 24"
			fill="none"
			stroke="currentColor"
			strokeWidth={2}
			strokeLinecap="round"
			strokeLinejoin="round"
			className={`inline-block shrink-0 ${SIZES[size]} ${className}`}
			role={label ? "img" : undefined}
			aria-label={label}
			aria-hidden={label ? undefined : true}
			{...props}
		>
			<path d={ICON_PATHS[name]} />
		</svg>
	);
}
