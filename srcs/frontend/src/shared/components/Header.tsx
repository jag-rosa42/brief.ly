import { useNavigate } from "react-router-dom";
import { useAuth } from "@/app/AuthContext";
import { Link } from "@/shared/components/Link"
import { Button } from "@/shared/components/Button"


export function Header() {
	const { isLoggedIn } = useAuth();

	return (
	<header className="flex justify-between items-center px-6 py-4">
		<Link to="/" variant="title">Brief<span className="text-secondary">.ly</span></Link>
		{isLoggedIn ? <NavbarLogged /> : <NavbarUnlogged />}
	</header>
	);
}

export function NavbarLogged(){
	const navigate = useNavigate();
	const { profileComplete, logout } = useAuth();
	return (
		<div className="flex gap-4">
			<Button
				type="submit"
				variant="primary"
				onClick={() => {
					logout();
					navigate("/");
				}}
			>
				Log out
			</Button>
			<Link
				to={profileComplete ? "/sidebar/brief" : "/sidebar/preferences"}
				variant="secondary"
			>
				{profileComplete ? "Morning Briefing" : "Preferences"}
			</Link>
		</div>
	);
}

export function NavbarUnlogged(){
	return (
		<div className="flex gap-4">
			<Link to="/login" variant="primary">Log in</Link>
			<Link to="/signup" variant="secondary">Sign up</Link>
		</div>
	);

}
