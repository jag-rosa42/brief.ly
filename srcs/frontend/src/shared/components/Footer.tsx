import { Link } from "react-router-dom";
export function Footer() {
	return (
		<footer className="p-6 flex flex-col">
			<nav className="font-serif flex gap-6 text-accent-dark">
				<Link to="/terms">Terms of Service</Link>
				<Link to="/privacy">Privacy Policy</Link>
			</nav>
		</footer>
	)
}