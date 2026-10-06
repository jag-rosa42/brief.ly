import { Navigate, Route, Routes } from "react-router-dom";
import { Layout } from "@/app/Layout";
import { LandingPage } from "@/pages/LandingPage";
import { TermsOfServicePage } from "@/pages/TermsOfServicePage";
import { PrivacyPolicyPage } from "@/pages/PrivacyPolicyPage";
import { NotFoundPage } from "@/pages/NotFoundPage";
import { DesignSystem } from "@/pages/DesignSystem";
import { SignupPage } from "@/pages/SignupPage";
import { LoginPage } from "@/pages/LoginPage";
import { ProfilePage } from "@/pages/ProfilePage";
import { NotificationTestPage } from "@/pages/NotificationTestPage";
import { useAuth } from "@/app/AuthContext";

export function AppRouter() {
	const { isLoggedIn } = useAuth();
	return (
		<Routes>
  			<Route element={<Layout />}>
				<Route index 
					element={<LandingPage />}/>
				<Route path="/termsofservice"
					element={<TermsOfServicePage />}/>
				<Route path="/privacypolicy"
					element={<PrivacyPolicyPage />}/>
				<Route path="/signup"
					element={<SignupPage />}/>
				<Route path="/login"
					element={<LoginPage/>}/>
				<Route path="/profile"
					element={
						isLoggedIn ? <ProfilePage/> : <Navigate to="/login" replace />}
					/>
				<Route path="/designsystem"
					element={<DesignSystem />}/>
				<Route path="/notificationtest"
					element={<NotificationTestPage />}/>
				<Route path="*"
					element={<NotFoundPage />}/>
			</Route>
		</Routes>
	);
}
