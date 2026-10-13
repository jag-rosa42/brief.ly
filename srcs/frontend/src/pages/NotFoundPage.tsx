import { Link } from "@/shared/components/Link";
import { Text } from "@/shared/components/Text";

export function NotFoundPage() {
	return (
		<main className="text-center py-32 px-6">
			<Text variant="title" className="text-6xl mb-4">404</Text>
			<Text variant="body" className="mb-8">
				This page doesn't exist - or it moved somewhere else.
			</Text>
			<Link to="/" variant="main">
				Go back home
			</Link>
		</main>
	);
}