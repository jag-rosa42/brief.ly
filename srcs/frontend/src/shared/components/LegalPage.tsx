import type { ReactNode } from "react";
import { Link } from "react-router-dom";

type LegalPageProps = {
	title: string;
	lastUpdated: string;
	children: ReactNode;
};

export function LegalPage({title, lastUpdated, children,}: LegalPageProps) {
	return (
		<main className="max-w-2xl mx-auto px-6 py-16">
			<h1 className="font-serif text-4xl font-bold text-primary mb-6">
				{title}
			</h1>

			<p className="text-accent leading-relaxed mb-10">
				Last updated: {lastUpdated}
			</p>

			{children}

			<Link to="/" className="text-primary underline mt-10 inline-block">
				Go back home
			</Link>
		</main>
	);
}


type LegalSectionProps = {
	title: string;
	children: ReactNode;
};

export function LegalSection({title,children,}: LegalSectionProps) {
	return (
		<section className="mb-8">
			<h2 className="font-sans text-2xl font-semibold text-secondary mb-3">
				{title}
			</h2>

			<div className="text-accent leading-relaxed">
				{children}
			</div>
		</section>
	);
}
