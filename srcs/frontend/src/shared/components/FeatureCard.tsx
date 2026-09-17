

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
			<Text variant="heading" className="mb-3">
				{title}
			</Text>

			<Text variant="body">
				{description}
			</Text>
		</div>
	);
}