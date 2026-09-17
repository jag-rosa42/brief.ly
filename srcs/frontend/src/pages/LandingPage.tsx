import { Link } from "@/shared/components/Link";
import { Division } from "@/shared/components/Division";
import { Text } from "@/shared/components/Text";


export function LandingPage() {
	return (
		<main>
			<section className="text-center text-primary pt-16 pb-10 px-6">
				<Text variant="title" className="text-5xl md:text-6xl tracking-tight mb-5">
					Build habits that actually stick
				</Text>
				<Text variant="lead" className="max-w-2xl mx-auto">					Flagrant Daily helps you track what matters, one small step at
					a time — no guilt, no noise, just steady progress.
				</Text>

				<div className="mt-7">
					<Link to="/signup" variant="main">
						Start the journey
					</Link>
				</div>
			</section>
			<section className="grid grid-cols-1 md:grid-cols-3 gap-6 px-6 pt-12 pb-12 max-w-6xl mx-auto">
				<Division variant="featurecard">
					<Text variant="heading">
						Track effortlessly
					</Text>
					<Text variant="body">
						Log your habits in seconds, right from your day-to-day routine — no friction, no forms to fill.
					</Text>
				</Division>
				<Division variant="featurecard">
					<Text variant="heading">
						Stay motivated
					</Text>
					<Text variant="body">
						See your progress build up over time, with gentle nudges that keep you going without the pressure.
					</Text>
				</Division>
				<Division variant="featurecard">
					<Text variant="heading">
						Make it yours
					</Text>
					<Text variant="body">
						Personalize what you track and how — the app adapts to your goals, not the other way around.
					</Text>
				</Division>
			</section>
		</main>
	);
}
