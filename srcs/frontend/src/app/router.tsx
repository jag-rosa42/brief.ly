import { Navigate, Route, Routes } from "react-router-dom";
import { Layout } from "./Layout";
import { LandingPage } from "../pages/LandingPage";
import { TermsOfServicePage } from "../pages/TermsOfServicePage";
import { PrivacyPolicyPage } from "../pages/PrivacyPolicyPage";
import { SignupPage } from "../pages/SignupPage";
import { LoginPage } from "../pages/LoginPage";
import { DashboardPage } from "../pages/DashboardPage";
import { ProfilePage } from "../pages/ProfilePage";
import { NotFoundPage } from "../pages/NotFoundPage";
import { useAuth } from "./AuthContext"

export function AppRouter() {
	const { isLoggedIn } = useAuth();
	return (
		<Routes>
			<Route
				path="/"
				element={
					<Layout>
						{isLoggedIn ? <DashboardPage /> : <LandingPage />}
					</Layout>
				}
			/>
			<Route
				path="/terms"
				element={
					<Layout>
						<TermsOfServicePage />
					</Layout>
				}
			/>
			<Route
				path="/privacy"
				element={
					<Layout>
						<PrivacyPolicyPage />
					</Layout>
				}
			/>
			<Route
				path="/signup"
				element={
					<Layout>
						{isLoggedIn ? <Navigate to="/" replace /> : <SignupPage />}
					</Layout>
				}
			/>
			<Route
				path="/login"
				element={
					<Layout>
						{isLoggedIn ? <Navigate to="/" replace /> : <LoginPage />}
					</Layout>
				}
			/>
			<Route
				path="/profile"
				element={
					<Layout>
						{isLoggedIn ? <ProfilePage /> : <Navigate to="/signup" replace />}
					</Layout>
				}
			/>
			<Route
				path="*"
				element={
					<Layout>
						<NotFoundPage />
					</Layout>
				}
			/>
		</Routes>
	);
}
