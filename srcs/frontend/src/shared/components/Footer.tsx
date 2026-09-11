import { Button } from "@/shared/components/Button";

export function Footer() {
	return (
		<footer className="bg-secondary p-6 flex flex-col">
			<nav  className="flex gap-6">
				<Button type="link" link="/terms" style ="Footer">Terms of Service</Button>
				<Button type="link" link="/privacy" style="Footer">Privacy Policy</Button>
			</nav>
		</footer>
	)
}