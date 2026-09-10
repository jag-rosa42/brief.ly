import { Link } from "react-router-dom";
export function TermsOfServicePage() {
	return (
		<main className="max-w-2xl mx-auto px-6 py-16">
			<h1 className="text-4xl font-bold text-primary mb-6">Terms of Service</h1>
			<p className="text-lg text-accent mb-4">
				We believe that building healthy habits shouldn't feel like a
				chore. Our mission is to make everyday wellness simple, personal,
				and genuinely enjoyable.
			</p>
			<p className="text-lg text-accent mb-4">
				Founded by a small team obsessed with good habits and better
				tools, we're building a product that adapts to you — not the
				other way around.
			</p>
			<div className="mt-10 border-l-4 border-accent pl-4">
				<p className="text-accent italic">
					"Small, consistent steps lead to lasting change — that's the
					idea behind everything we build."
				</p>
			</div>
			<Link to="/" className="text-primary underline mt-10 inline-block">
				Go back home
			</Link>
		</main>
	);
}
