import { useNavigate } from "react-router-dom";
import { useAuth } from "@/app/AuthContext"
import { Button } from "@/shared/components/Button"

export function Header(){
    const { isLoggedIn } = useAuth();
	return (
    <header className="flex justify-between items-center px-6 py-4">
        <Button type="link" link="/" style="Title">The Focus Times</Button>
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
            <Button type="button" onClick={handleLogout} style="Header1">Log out</Button>
            <Button type="link" link="/profile" style="Header2">Profile</Button>
        </div>
    );
}

export function HeaderUnlogged(){
    return (
        <div className="flex gap-4">
            <Button type="link" link="/login" style="Header1">Log in</Button>
            <Button type="link" link="/signup" style="Header2">Sign up</Button>
        </div>
    );
}