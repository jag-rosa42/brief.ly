import { Navigate, Route, Routes } from "react-router-dom";
import { Layout } from "@/app/Layout";
import { LandingPage } from "@/pages/LandingPage";
import { TermsOfServicePage } from "@/pages/TermsOfServicePage";
import { PrivacyPolicyPage } from "@/pages/PrivacyPolicyPage";
import { SignupPage } from "@/pages/SignupPage";
import { LoginPage } from "@/pages/LoginPage";
import { DashboardPage } from "@/pages/DashboardPage";
import { ProfilePage } from "@/pages/ProfilePage";
import { NotFoundPage } from "@/pages/NotFoundPage";
import { useAuth } from "@/app/AuthContext"

export function AppRouter() {
	const { isLoggedIn } = useAuth();
	return (
		<Routes>
  			<Route element={<Layout />}>
				<Route index 
					element={isLoggedIn ? <DashboardPage /> : <LandingPage />}/>
				<Route path="/terms"
					element={<TermsOfServicePage />}/>
				<Route path="/privacy"
					element={<PrivacyPolicyPage />}/>
				<Route path="/signup"
					element={isLoggedIn ? <Navigate to="/" replace /> : <SignupPage />}/>
				<Route path="/login"
					element={isLoggedIn ? <Navigate to="/" replace /> : <LoginPage />}/>
				<Route path="/profile"
					element={isLoggedIn ? <ProfilePage /> : <Navigate to="/signup" replace />}/>
				<Route path="*"
					element={<NotFoundPage />}/>
			</Route>
		</Routes>
	);
}
