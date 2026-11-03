import { Navigate, Outlet, Route, Routes, useLocation } from "react-router-dom";
import { useEffect, useState } from "react";
import { Layout } from "@/app/Layout";
import { LandingPage } from "@/pages/LandingPage";
import { TermsOfServicePage } from "@/pages/TermsOfServicePage";
import { PrivacyPolicyPage } from "@/pages/PrivacyPolicyPage";
import { NotFoundPage } from "@/pages/NotFoundPage";
import { SignupPage } from "@/pages/SignupPage";
import { LoginPage } from "@/pages/LoginPage";
import { DashboardPage } from "@/pages/DashboardPage";
import { useAuth } from "@/app/useAuth";
import { Spinner } from "@/shared/components/Spinner";

import { DASHBOARD_TABS, LAST_PATH, GUEST_PATHS } from "@/app/navigation";

function LastPathTracker() {
	const { isLoggedIn, isLoading } = useAuth();
	const location = useLocation();

	useEffect(() => {
		if (isLoading || !isLoggedIn)
			return;
		if (GUEST_PATHS.includes(location.pathname))
			return;
		sessionStorage.setItem(LAST_PATH, location.pathname);
	}, [isLoading, isLoggedIn, location.pathname]);

	return null;
}

function ProtectedRoute() {
	const { isLoggedIn, isLoading } = useAuth();

	if (isLoading)
		return <Spinner />;
	if (!isLoggedIn)
		return (<Navigate to="/" replace />)
	return (<Outlet />);
}

function GuestRoute() {
	const { isLoggedIn, isLoading, profileComplete } = useAuth();
	const [lastPath] = useState(() => sessionStorage.getItem(LAST_PATH));

	if (isLoading)
		return <Spinner />;
	if (isLoggedIn) {
		let target = "/dashboard/profile";

		if (profileComplete)
			target = "/dashboard/brief";
		if (lastPath && !GUEST_PATHS.includes(lastPath))
			target = lastPath;
		return (<Navigate to={target} replace />);
	}
	return (<Outlet />);
}

export function AppRouter() {
	return (
		<>
			<LastPathTracker />
			<Routes>
				<Route element={<Layout />}>
					<Route index
						element={<LandingPage />} />
					<Route path="/termsofservice"
						element={<TermsOfServicePage />} />
					<Route path="/privacypolicy"
						element={<PrivacyPolicyPage />} />
					<Route element={<GuestRoute />}>
						<Route path="/signup"
							element={<SignupPage />} />
						<Route path="/login"
							element={<LoginPage />} />
					</Route>
					<Route path="*"
						element={<NotFoundPage />} />
				</Route>
				<Route element={<ProtectedRoute />}>
					{DASHBOARD_TABS.map((tab) => (
						<Route key={tab} path={`/dashboard/${tab}`} element={<DashboardPage tab={tab} />} />
					))}
					<Route path="/dashboard" element={<Navigate to="/dashboard/brief" replace />} />
				</Route>
			</Routes>
		</>
	);
}