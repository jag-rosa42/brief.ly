import { Link } from "@/shared/components/Link";

export function Footer() {
	return (
		<footer className="bg-secondary p-6 flex flex-col">
			<nav  className="flex gap-6">
				<Link to="/terms" variant="text">Terms of Service</Link>
				<Link to="/privacy" variant="text">Privacy Policy</Link>
			</nav>
		</footer>
	)
}