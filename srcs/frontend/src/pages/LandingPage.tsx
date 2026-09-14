import { Link } from "react-router-dom";
import { FeatureCard } from "../shared/components/FeatureCard";


export function LandingPage() {
	return (
		<main>
			<section className="text-center text-primary pt-16 pb-10 px-6">
				<h1 className="font-serif text-5xl md:text-6xl font-bold tracking-tight mb-5">
					Build habits that actually stick
				</h1>

				<p className="font-serif text-lg md:text-xl text-accent-dark max-w-2xl mx-auto">
					Flagrant Daily helps you track what matters, one small step at
					a time — no guilt, no noise, just steady progress.
				</p>

				<div className="mt-7">
<Link
						to="/signup"
						className="bg-accent-dark text-background px-5 py-2.5 rounded"
					>
						Start the journey
					</Link>
				</div>
			</section>

			<section className="grid grid-cols-1 md:grid-cols-3 gap-6 px-6 pt-12 pb-12 max-w-6xl mx-auto">
				<FeatureCard
					title="Track effortlessly"
					description="Log your habits in seconds, right from your day-to-day routine — no friction, no forms to fill."
				/>

				<FeatureCard
					title="Stay motivated"
					description="See your progress build up over time, with gentle nudges that keep you going without the pressure."
				/>

				<FeatureCard
					title="Make it yours"
					description="Personalize what you track and how — the app adapts to your goals, not the other way around."
				/>
			</section>
		</main>
	);
}
