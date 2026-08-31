export function LandingPage() {
	return (
		<main>
			<section className="text-center text-primary py-24 px-6">
				<h1 className="text-5xl font-bold mb-4">
					Build habits that actually stick
				</h1>
				<p className="text-lg text-accent max-w-xl mx-auto">
					Flagrant Daily helps you track what matters, one small step at
					a time — no guilt, no noise, just steady progress.
				</p>
			</section>

			<section className="grid grid-cols-1 md:grid-cols-3 gap-8 px-6 py-16 max-w-5xl mx-auto">
				<div>
					<h2 className="font-semibold text-xl mb-2 text-primary">
						Track effortlessly
					</h2>
					<p className="text-accent">
						Log your habits in seconds, right from your day-to-day
						routine — no friction, no forms to fill.
					</p>
				</div>
				<div>
					<h2 className="font-semibold text-xl mb-2 text-primary">
						Stay motivated
					</h2>
					<p className="text-accent">
						See your progress build up over time, with gentle nudges
						that keep you going without the pressure.
					</p>
				</div>
				<div>
					<h2 className="font-semibold text-xl mb-2 text-primary">
						Make it yours
					</h2>
					<p className="text-accent">
						Personalize what you track and how — the app adapts to
						your goals, not the other way around.
					</p>
				</div>
			</section>
		</main>
	);
}
