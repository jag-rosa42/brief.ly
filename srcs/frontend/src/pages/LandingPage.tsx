import { Link } from "@/shared/components/Link";
import { Division } from "@/shared/components/Division";
import { Text } from "@/shared/components/Text";
import { useAuth } from "@/app/AuthContext";

export function LandingPage() {
	const { isLoggedIn, profileComplete } = useAuth();

	let startLink = "/signup";
	if (isLoggedIn) {
		startLink = profileComplete ? "/sidebar/brief" : "/sidebar/preferences";
	}
	return (
		<main>
			<section className="text-center text-primary pt-16 pb-10 px-6">
				<Text variant="title" className="text-5xl md:text-6xl tracking-tight mb-5">
					Your daily digest, tuned to what actually matters to you
				</Text>
				<Text variant="lead" className="max-w-2xl mx-auto">
					Brief.ly reads the sources so you don't have to —
					pick your topics, and get sharp, personalized summaries
					delivered every day.
				</Text>

				<div className="mt-7">
					<Link
						to={startLink}
						variant="main">
						Start the journey
					</Link>
				</div>
			</section>
			<section className="grid grid-cols-1 md:grid-cols-3 gap-6 px-6 pt-12 pb-12 max-w-6xl mx-auto">
				<Division variant="featurecard">
					<Text variant="heading">
						Pick your topics
					</Text>
					<Text variant="body">
						Tell us what you care about — AI, finance, science,
						whatever — and we'll build your feed around it.
					</Text>
				</Division>
				<Division variant="featurecard">
					<Text variant="heading">
						Get the essence, fast
					</Text>
					<Text variant="body">
						Every article, boiled down to what matters. No fluff,
						no clickbait, just the key points.
					</Text>
				</Division>
				<Division variant="featurecard">
					<Text variant="heading">
						Stay ahead, not overwhelmed
					</Text>
					<Text variant="body">
						A daily digest that respects your time — skim in
						minutes, stay genuinely informed.
					</Text>
				</Division>
			</section>
		</main>
	);
}
