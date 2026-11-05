import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import "@fontsource-variable/fraunces";
import "@fontsource-variable/sofia-sans";
import "@/index.css";
import App from "@/App.tsx";
import { AuthProvider } from "@/app/AuthContext";
import { SavedArticlesProvider } from "@/app/SavedArticlesContext";
import { PreferencesProvider } from "@/app/PreferencesContext";

createRoot(document.getElementById("root")!).render(
	<StrictMode>
		<BrowserRouter>
			<AuthProvider>
				<PreferencesProvider>
					<SavedArticlesProvider>
						<App />
					</SavedArticlesProvider>
				</PreferencesProvider>
			</AuthProvider>
		</BrowserRouter>
	</StrictMode>,
);
