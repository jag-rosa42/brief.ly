import { Link } from "react-router-dom";

export function PrivacyPage() {
	return (
		<main className="max-w-2xl mx-auto px-6 py-16">
			<h1 className="text-4xl font-bold text-primary mb-6">Privacy</h1>
			<p className="text-lg text-gray-700 mb-10">
				Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do
				eiusmod tempor incididunt ut labore et dolore magna aliqua.
			</p>

			<section className="mb-8">
				<h2 className="text-2xl font-semibold text-secondary mb-3">
					Information We Collect
				</h2>
				<p className="text-gray-700">
					Ut enim ad minim veniam, quis nostrud exercitation ullamco
					laboris nisi ut aliquip ex ea commodo consequat. Duis aute
					irure dolor in reprehenderit in voluptate velit esse cillum
					dolore eu fugiat nulla pariatur.
				</p>
			</section>

			<section className="mb-8">
				<h2 className="text-2xl font-semibold text-secondary mb-3">
					How We Use Your Information
				</h2>
				<p className="text-gray-700">
					Excepteur sint occaecat cupidatat non proident, sunt in culpa
					qui officia deserunt mollit anim id est laborum. Sed ut
					perspiciatis unde omnis iste natus error sit voluptatem
					accusantium doloremque laudantium.
				</p>
			</section>

			<section className="mb-8">
				<h2 className="text-2xl font-semibold text-secondary mb-3">
					Cookies
				</h2>
				<p className="text-gray-700">
					Nemo enim ipsam voluptatem quia voluptas sit aspernatur aut
					odit aut fugit, sed quia consequuntur magni dolores eos qui
					ratione voluptatem sequi nesciunt.
				</p>
			</section>

			<section>
				<h2 className="text-2xl font-semibold text-secondary mb-3">
					Contact Us
				</h2>
				<p className="text-gray-700">
					Neque porro quisquam est, qui dolorem ipsum quia dolor sit
					amet, consectetur, adipisci velit, sed quia non numquam eius
					modi tempora incidunt ut labore et dolore magnam aliquam.
				</p>
			</section>

			<Link to="/" className="text-primary underline mt-10 inline-block">
				Go back home
			</Link>
		</main>
	);
}
