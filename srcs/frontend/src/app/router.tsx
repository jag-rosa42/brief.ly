import { Route, Routes } from "react-router-dom";
import { Layout } from "@/app/Layout";
import { LandingPage } from "@/pages/LandingPage";
import { TermsOfServicePage } from "@/pages/TermsOfServicePage";
import { PrivacyPolicyPage } from "@/pages/PrivacyPolicyPage";
import { NotFoundPage } from "@/pages/NotFoundPage";
import { DesignSystem } from "@/pages/DesignSystem";


export function AppRouter() {
	return (
		<Routes>
  			<Route element={<Layout />}>
				<Route index 
					element={<LandingPage />}/>
				<Route path="/terms"
					element={<TermsOfServicePage />}/>
				<Route path="/privacy"
					element={<PrivacyPolicyPage />}/>
				<Route path="/designsystem"
					element={<DesignSystem />}/>
				<Route path="*"
					element={<NotFoundPage />}/>
			</Route>
		</Routes>
	);
}
