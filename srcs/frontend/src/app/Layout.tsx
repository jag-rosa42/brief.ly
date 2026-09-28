import { Outlet } from "react-router-dom";
import { Footer } from "@/shared/components/Footer";
import { Header } from "@/shared/components/Header";

export function Layout() {
	return (
		<div className="bg-background min-h-screen flex flex-col">
			<Header />
			<div className="flex-1"><Outlet /></div>
			<Footer />
		</div>
	);
}
