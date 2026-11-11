import { StaticPage, StaticSection } from "@/shared/components/StaticPage";

export function TermsOfServicePage() {
	return (
		<StaticPage title="Terms of Service" lastUpdated="November 11th, 2026">
			<StaticSection title="1. Acceptance of Terms">
				<p>
					By creating an account or using Brief.ly, you agree to these Terms of Service. If you do
					not agree with them, please do not use the service.
				</p>
			</StaticSection>

			<StaticSection title="2. About Brief.ly">
				<p>
					Brief.ly is a student project made at 42, not a commercial service. It gathers articles on
					the topics you follow and shows them in a daily brief, with short summaries. It may
					change, or be unavailable, as the project evolves.
				</p>
			</StaticSection>

			<StaticSection title="3. Your Account">
				<p>
					You are responsible for giving accurate information when you sign up, for keeping your
					password secure, and for what happens through your account. Contact us if you think
					someone else has used it.
				</p>
			</StaticSection>

			<StaticSection title="4. Acceptable Use">
				<p>
					Use Brief.ly responsibly and only for lawful purposes. Don't try to interfere with the
					service, to access other accounts or systems, or to use it in a way that could harm other
					users or the service itself.
				</p>
			</StaticSection>

			<StaticSection title="5. AI-Generated Summaries">
				<p>
					The summaries are written automatically by an AI model. They can be incomplete, outdated
					or wrong, and they don't replace the original articles: for anything important, read the
					source, linked on each article.
				</p>
			</StaticSection>

			<StaticSection title="6. Public API and API Keys">
				<p>
					You can create API keys to use Brief.ly from your own programs. Each key acts on your
					account with the scopes you chose, and expires after 48 hours. Keep your keys secret:
					anyone who has one can use it. Revoke a key you no longer need, or one that may have
					leaked. Requests are rate-limited, and we may revoke keys that are abused.
				</p>
			</StaticSection>

			<StaticSection title="7. Intellectual Property">
				<p>
					The articles, and the names and trademarks of their publishers, belong to their owners.
					Brief.ly only shows a short summary and links to the original.
				</p>
			</StaticSection>

			<StaticSection title="8. Availability of the Service">
				<p>
					We don't guarantee that Brief.ly is always available: it may be down for maintenance,
					technical issues, or the end of the project.
				</p>
			</StaticSection>

			<StaticSection title="9. Account Termination">
				<p>
					You may stop using Brief.ly at any time, and ask the team to delete your account and its
					data. We may suspend an account used against these terms.
				</p>
			</StaticSection>

			<StaticSection title="10. Changes to These Terms">
				<p>
					We may update these terms. When we do, we update the date at the top of this page. Using
					the service after a change means you accept the new terms.
				</p>
			</StaticSection>

			<StaticSection title="11. Contact">
				<p>If you have any questions, please contact us at contact@brief.ly.</p>
			</StaticSection>
		</StaticPage>
	);
}
