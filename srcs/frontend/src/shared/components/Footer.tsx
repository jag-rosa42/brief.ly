import { Link } from "react-router-dom";
export function Footer() {
	return (
		<footer className="bg-secondary p-6 ">
			<nav className="flex gap-6 text-background">
				<Link to="/about">About Us</Link>
				<Link to="/privacy">Privacy</Link>
			</nav>
		</footer>
	)
}