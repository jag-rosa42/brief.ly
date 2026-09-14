type FeatureCardProps = {
	title: string;
	description: string;
};

export function FeatureCard({
	title,
	description,
}: FeatureCardProps) {
	return (
		<div className="bg-white border border-ui rounded-xl p-6">
			<h2 className="font-sans font-semibold text-xl text-accent-dark mb-3">
				{title}
			</h2>

			<p className="text-accent leading-relaxed">
				{description}
			</p>
		</div>
	);
}