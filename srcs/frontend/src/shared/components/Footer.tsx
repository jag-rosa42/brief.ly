import { Link } from "react-router-dom";
export function Footer() {
	return (
		<footer className="bg-secondary p-6 flex flex-col">
			<nav className="flex gap-6 text-background">
				<Link to="/terms">Terms of Service</Link>
				<Link to="/privacy">Privacy Policy</Link>
			</nav>
		</footer>
	)
}