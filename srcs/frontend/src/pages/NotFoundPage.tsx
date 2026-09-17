import { Link } from "@/shared/components/Link";

export function NotFoundPage() {
	return (
		<main className="text-center py-32 px-6">
			<p className="text-6xl font-bold text-primary mb-4">404</p>
			<p className="text-lg text-gray-600 mb-8">
				This page doesn't exist — or it moved somewhere else.
			</p>
			<Link to="/" variant="main">
				Go back home
			</Link>
		</main>
	);
}