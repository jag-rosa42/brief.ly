import { useNavigate } from "react-router-dom";
import { useAuth } from "@/app/AuthContext"
import { Button } from "@/shared/components/Button"
import { Link } from "@/shared/components/Link"

export function Header(){
    const { isLoggedIn } = useAuth();
	return (
    <header className="flex justify-between items-center px-6 py-4">
        <Link to="/" variant="title">The Focus Times</Link>
        {isLoggedIn ? <HeaderLogged /> : <HeaderUnlogged />}
    </header>
	)
}

export function HeaderLogged(){
    const { logout } = useAuth();
    const navigate = useNavigate();

    function handleLogout() {
        logout();
        navigate("/");
    }

    return (
        <div className="flex gap-4">
            <Button type="button" onClick={handleLogout} variant="primary">Log out</Button>
            <Link to="/profile" variant="secondary">Profile</Link>
        </div>
    );
}

export function HeaderUnlogged(){
    return (
        <div className="flex gap-4">
            <Link to="/login" variant="primary">Log in</Link>
            <Link to="/signup" variant="secondary">Sign up</Link>
        </div>
    );
}