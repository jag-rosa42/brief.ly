import { StaticPage, StaticSection } from "@/shared/components/StaticPage";
import { Text } from "@/shared/components/Text";

export function PrivacyPolicyPage() {
	return (
		<StaticPage title="Privacy Policy" lastUpdated="November 11th, 2026">
			<Text variant="body" className="mb-8">
				Brief.ly is a student project made at 42. This page explains what it stores about you and
				why.
			</Text>

			<StaticSection title="1. What Information Do We Gather About You?">
				<ul className="list-disc space-y-1 pl-5">
					<li>
						Your account: your email address and your password. The password is never stored as is,
						only as a hash.
					</li>
					<li>Your profile: the name you choose and the topics you follow.</li>
					<li>Your saved articles (up to 12).</li>
					<li>
						Your API keys, if you create any: their name, scopes and dates. The key itself is shown
						once, then only stored as a hash.
					</li>
					<li>
						Our server logs record the IP address and the page of each request, for security and
						debugging.
					</li>
				</ul>
			</StaticSection>

			<StaticSection title="2. How Do We Use Your Information?">
				<p>
					Only to run the service: to sign you in, to build your daily brief from your topics, to
					keep your saved articles, and to let your programs use the public API with your keys. We
					don't use it for advertising or profiling.
				</p>
			</StaticSection>

			<StaticSection title="3. How Do We Use Cookies?">
				<p>
					We use a single cookie, which keeps you signed in for up to 7 days. It can't be read by
					the page's scripts and is only sent to our own site. Your browser also keeps a small
					sign-in marker and the last page you visited, so you get back to it after reloading. There
					are no advertising or tracking cookies.
				</p>
			</StaticSection>

			<StaticSection title="4. To Whom Do We Disclose or Share the Data We Gather?">
				<p>
					To no one. We don't sell or share your data. The articles come from NewsAPI, but we never
					send it anything about you, and the summaries are written by an AI model that runs on our
					own server.
				</p>
			</StaticSection>

			<StaticSection title="5. How Do We Protect Your Data?">
				<p>
					Passwords and API keys are stored only as hashes, all traffic goes through HTTPS, and the
					public API is rate-limited. No online service can guarantee complete security, though.
				</p>
			</StaticSection>

			<StaticSection title="6. What Are Your Rights and Choices?">
				<p>
					You can see and change your profile and saved articles at any time, and revoke your API
					keys. There is no button to delete your account yet: to have your account and its data
					deleted, contact the team (see below).
				</p>
			</StaticSection>

			<StaticSection title="7. How Are Changes to this Privacy Policy Communicated?">
				<p>We will post any change on this page and update the date at the top.</p>
			</StaticSection>

			<StaticSection title="8. How Can You Contact Us?">
				<p>If you have any questions, please contact us at contact@brief.ly.</p>
			</StaticSection>
		</StaticPage>
	);
}
