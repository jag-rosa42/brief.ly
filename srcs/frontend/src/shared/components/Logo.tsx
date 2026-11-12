import { Link } from "@/shared/components/Link";

export function Logo() {
	return (
		<Link to="/" variant="title" className="inline-flex items-center gap-2">
			{/* The same file as the browser tab icon (public/favicon.svg), so both stay
			    identical. alt is empty: the name next to it already says what it is. */}
			<img src="/favicon.svg" alt="" className="size-8" />
			<span>
				Brief<span className="text-secondary">.ly</span>
			</span>
		</Link>
	);
}
