import { Link } from "@/shared/components/Link";

export function Logo() {
	return (
		<Link to="/" variant="title">
			Brief<span className="text-secondary">.ly</span>
		</Link>
	);
}