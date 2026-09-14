import { LegalPage,LegalSection,} from "../shared/components/LegalPage";

export function TermsOfServicePage() {
	return (
		<LegalPage title="Terms of Service" lastUpdated="September 11th, 2026">
			<LegalSection title="1. Acceptance of Terms">
				<p>
					By creating an account or using Flagrant Daily, you agree to
					these Terms of Service. If you do not agree with these terms,
					please do not use the service.
				</p>
			</LegalSection>

			<LegalSection title="2. Content of the Services">
				<p>
					Flagrant Daily is a service designed to help users discover
					and follow daily article summaries through a personal
					dashboard.
				</p>

				<p className="mt-3">
					The service may be updated, modified, or temporarily
					unavailable as we continue to develop and improve it.
				</p>
			</LegalSection>

			<LegalSection title="3. Your Account">
				<p>
					You are responsible for providing accurate information when
					creating your account and for keeping your account
					credentials secure.
				</p>

				<p className="mt-3">
					You are responsible for all activity that occurs through your
					account. Please contact us if you believe that your account
					has been accessed without your permission.
				</p>
			</LegalSection>

			<LegalSection title="4. Acceptable Use">
				<p>
					You agree to use Flagrant Daily responsibly and only for
					lawful purposes.
				</p>

				<p className="mt-3">
					You must not attempt to interfere with the service, gain
					unauthorized access to other accounts or systems, abuse the
					service, or use it in a way that could harm other users or
					the service itself.
				</p>
			</LegalSection>

			<LegalSection title="5. Article Summaries">
				<p>
					Flagrant Daily provides summaries of articles from external
					sources. These summaries are intended to help users quickly
					understand the main topics and are not a replacement for
					reading the original articles.
				</p>

				<p className="mt-3">
					We do not guarantee that summaries are always complete,
					accurate, or up to date. For important information, you
					should always consult the original source.
				</p>
			</LegalSection>

			<LegalSection title="6. Intellectual Property">
				<p>
					The Flagrant Daily name, design, interface, and original
					software are owned by the project team and
					may not be copied, modified, or redistributed without
					permission.
				</p>

				<p className="mt-3">
					Article content and trademarks belonging to third parties
					remain the property of their respective owners.
				</p>
			</LegalSection>

			<LegalSection title="7. Availability of the Service">
				<p>
					We aim to keep Flagrant Daily available and reliable, but we
					do not guarantee uninterrupted access to the service.
				</p>

				<p className="mt-3">
					The service may occasionally be unavailable due to
					maintenance, technical issues, or circumstances beyond our
					control.
				</p>
			</LegalSection>

			<LegalSection title="8. Account Termination">
				<p>
					You may stop using the service and request the deletion of
					your account at any time.
				</p>

				<p className="mt-3">
					We may suspend or terminate an account if it is used in
					violation of these Terms of Service or in a way that could
					harm the service or other users.
				</p>
			</LegalSection>

			<LegalSection title="9. Changes to These Terms">
				<p>
					We may update these Terms of Service from time to time. When
					we make changes, we will update the date at the top of this
					page. Continued use of the service after changes are made
					means that you accept the updated terms.
				</p>
			</LegalSection>

			<LegalSection title="10. Contact">
				<p>
					If you have any questions about these Terms of Service, please
					contact us at FlagrantDaily@contact.fr.
				</p>
			</LegalSection>
		</LegalPage>
	);
}


