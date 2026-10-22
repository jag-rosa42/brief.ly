import { Navigate, Outlet, Route, Routes } from "react-router-dom";
import { Layout } from "@/app/Layout";
import { LandingPage } from "@/pages/LandingPage";
import { TermsOfServicePage } from "@/pages/TermsOfServicePage";
import { PrivacyPolicyPage } from "@/pages/PrivacyPolicyPage";
import { NotFoundPage } from "@/pages/NotFoundPage";
import { SignupPage } from "@/pages/SignupPage";
import { LoginPage } from "@/pages/LoginPage";
import { DashboardPage } from "@/pages/DashboardPage";
//import { NotificationTestPage } from "@/pages/NotificationTestPage";
import { useAuth } from "@/app/useAuth";
import { ApiKeyPage } from "@/pages/ApiKeyPage";
import { Spinner } from "@/shared/components/Spinner";

function ProtectedRoute() {
	const { isLoggedIn, isLoading } = useAuth();
	if (isLoading)
		return <Spinner />;
	return (isLoggedIn ? <Outlet /> : <Navigate to="/" replace />);
}

export function AppRouter() {
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
				{/*<Route path="/notificationtest"
					element={<NotificationTestPage />}/>*/}
				<Route path="*"
					element={<NotFoundPage />}/>
			</Route>
				<Route element={<ProtectedRoute />}>
  					<Route path="/api-keys" element={<ApiKeyPage />} />
					<Route path="/dashboard/:tab" element={<DashboardPage />} />
					<Route path="/dashboard" element={<Navigate to="/dashboard/brief" replace />} />
			</Route>
		</Routes>
	);
}