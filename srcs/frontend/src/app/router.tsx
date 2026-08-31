import { Route, Routes } from "react-router-dom";
import { Layout } from "./Layout";
import { LandingPage } from "../pages/LandingPage";
import { AboutPage } from "../pages/AboutPage";
import { PrivacyPage } from "../pages/PrivacyPage";
import { NotFoundPage } from "../pages/NotFoundPage";

export function AppRouter() {
	return (
		<Routes>
			<Route
				path="/"
				element={
					<Layout>
						<LandingPage />
					</Layout>
				}
			/>
			<Route
				path="/about"
				element={
					<Layout>
						<AboutPage />
					</Layout>
				}
			/>
			<Route
				path="/privacy"
				element={
					<Layout>
						<PrivacyPage />
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
