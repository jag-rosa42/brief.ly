import { useAuth } from "@/app/useAuth";
import { Link } from "@/shared/components/Link";
import { Button } from "@/shared/components/Button";
import { Logo } from "@/shared/components/Logo";
import { useLogout } from "@/app/useLogout";

export function Header() {
	const { isLoggedIn } = useAuth();

	return (
		<header className="flex justify-between items-center px-6 py-4">
			<Logo />
			{isLoggedIn ? <NavbarLogged /> : <NavbarUnlogged />}
		</header>
	);
}

export function NavbarLogged() {
	const { profileComplete } = useAuth();
	const logout = useLogout();

	return (
		<div className="flex gap-4">
			<Button
				type="submit"
				variant="primary"
				onClick={() => {
					void logout();
				}}
			>
				Log out
			</Button>
			<Link to={profileComplete ? "/dashboard/brief" : "/dashboard/profile"} variant="secondary">
				{profileComplete ? "Morning Briefing" : "Profile"}
			</Link>
		</div>
	);
}

export function NavbarUnlogged() {
	return (
		<div className="flex gap-4">
			<Link to="/login" variant="primary">
				Log in
			</Link>
			<Link to="/signup" variant="secondary">
				Sign up
			</Link>
		</div>
	);
}
