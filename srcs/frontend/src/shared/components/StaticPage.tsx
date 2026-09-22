import type { ReactNode } from "react";
import { Link } from "@/shared/components/Link";
import { Text } from "@/shared/components/Text";
import { Division } from "@/shared/components/Division";

interface StaticPageProps {
	title: string;
	lastUpdated: string;
	children: ReactNode;
}

export function StaticPage({title, lastUpdated, children,}: StaticPageProps) {
	return (
		<main className="max-w-2xl mx-auto px-6 py-16">
			<Text variant="title" className="mb-6">
				{title}
			</Text>
			
			<Text variant="body" className="mb-10">
				Last updated: {lastUpdated}
			</Text>

			{children}

			<Link to="/" variant="main">
				Go back home
			</Link>
		</main>
	);
}


interface StaticSectionProps {
	title: string;
	children: ReactNode;
}

export function StaticSection({title,children,}: StaticSectionProps) {
	return (
		<section className="mb-8">
			<Text variant="subheading" className="mb-3">
				{title}
			</Text>

			<Division variant="content">
				{children}
			</Division>
		</section>
	);
}
