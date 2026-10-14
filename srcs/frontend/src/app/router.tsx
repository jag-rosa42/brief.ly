import { Navigate, Route, Routes } from "react-router-dom";
import { Layout } from "@/app/Layout";
import { LandingPage } from "@/pages/LandingPage";
import { TermsOfServicePage } from "@/pages/TermsOfServicePage";
import { PrivacyPolicyPage } from "@/pages/PrivacyPolicyPage";
import { NotFoundPage } from "@/pages/NotFoundPage";
import { DesignSystem } from "@/pages/DesignSystem";
import { SignupPage } from "@/pages/SignupPage";
import { LoginPage } from "@/pages/LoginPage";
import { SidebarPage } from "@/pages/SidebarPage";
//import { NotificationTestPage } from "@/pages/NotificationTestPage";
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
				<Route path="/designsystem"
					element={<DesignSystem />}/>
				{/*<Route path="/notificationtest"
					element={<NotificationTestPage />}/>*/}
				<Route path="*"
					element={<NotFoundPage />}/>
			</Route>
			<Route 
				path="/sidebar"
				element={<Navigate to="/sidebar/brief" replace />}/>
			<Route 
				path="/sidebar/:tab"
				element={
					isLoggedIn ? <SidebarPage /> : <Navigate to="/" replace />
				}
				/>
		</Routes>
	);
}