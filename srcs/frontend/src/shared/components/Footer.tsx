import { Link } from "@/shared/components/Link";

export function Footer() {
	return (
		<footer className="p-6 flex flex-col border-t border-accent-dark">
			<nav className=" flex gap-6 font-serif text-accent-dark">
				<Link to="/termsofservice" variant="simple">Terms of Service</Link>
				<Link to="/privacypolicy" variant="simple">Privacy Policy</Link>
			</nav>
		</footer>
	)
}