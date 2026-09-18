import { Outlet } from "react-router-dom";
import { Footer } from "@/shared/components/Footer";
import { Header } from "@/shared/components/Header";

export function Layout() {
	return (
		<div className="bg-background min-h-screen flex flex-col">
			<Header />
			<main className="flex-1"><Outlet /></main>
			<Footer />
		</div>
	);
}
