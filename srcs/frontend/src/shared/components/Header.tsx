import { useNavigate } from "react-router-dom";
import { useAuth } from "@/app/AuthContext"
import { Link } from "@/shared/components/Link"
import { Button } from "@/shared/components/Button"


export function Header() {
    const { isLoggedIn } = useAuth();
	return (
    <header className="flex justify-between items-center px-6 py-4">
        <Link to="/" variant="title">Flagrant Daily</Link>
        {isLoggedIn ? <HeaderLogged /> : <HeaderUnlogged />}
    </header>
	)
}


export function HeaderLogged(){
    const { logout } = useAuth();
    const navigate = useNavigate();

    return (

        <div className="flex gap-4">
            <Button type="submit" onClick={() => { logout(); navigate("/"); }} variant="primary">Log out</Button>
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