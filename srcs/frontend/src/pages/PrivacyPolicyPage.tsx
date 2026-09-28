
import { StaticPage,StaticSection,} from "@/shared/components/StaticPage";

export function PrivacyPolicyPage() {
	return (
		<StaticPage title="Privacy Policy" lastUpdated="September 14th, 2026">
			<StaticSection title="1. What Information Do We Gather About You?">
				<p>
					When you use our service, we may collect information that is
					necessary to create and manage your account and provide a
					complete experience.
				</p>
			</StaticSection>

			<StaticSection title="2. How Do We Use Your Information?">
				<p>
					We use your information to provide and maintain the service and 
					authenticate your account.
				</p>
			</StaticSection>

			<StaticSection title="3. What About Third-Party Authentication?">
				<p>
					You may be able to sign in using a third-party authentication
					provider. If you choose this option, the provider may share
					certain account information with us in accordance with your
					authorization and their privacy policy.
				</p>
			</StaticSection>

			<StaticSection title="4. How Do We Use Cookies?">
				<p>
					We may use cookies or similar technologies that are necessary
					to keep you authenticated and maintain your session.
					We do not use cookies for advertising purposes.
				</p>
			</StaticSection>

			<StaticSection title="5. To Whom Do We Disclose or Share the Data We Gather?">
				<p>
					We do not sell your personal information. Your information is
					only shared with third-party services when necessary to
					provide authentication, storage, or other essential
					features of the application.
				</p>
			</StaticSection>

			<StaticSection title="6. How Do We Protect Your Data?">
				<p>
					We take reasonable measures to protect your information from
					unauthorized access, alteration, disclosure, or destruction.
					However, no online service can guarantee complete security.
				</p>
			</StaticSection>

			<StaticSection title="7. What Are Your Rights and Choices?">
				<p>
					You may request access to, correction of, or deletion of your
					personal information. You may also request the deletion of
					your account and associated data.
				</p>
			</StaticSection>

			<StaticSection title="8. How Are Changes to this Privacy Policy Communicated?">
				<p>
					We will post any changes on this page by updating this policy. If we make a significant or material change in the way we collect, 
					use or share your personal information, we will notify you via email or prominent notice within the website. If you object to any change, you can stop using the website Services.
					After we post any changes on this page, your continued use of the website Services is subject to the updated Privacy Policy.
				</p>
			</StaticSection>

			<StaticSection title="9. How Can You Contact Us?">
				<p>
					If you have any questions about this Privacy Policy or how
					your data is handled, please contact us at contact@brief.ly.
				</p>
			</StaticSection>
		</StaticPage>
	);
}