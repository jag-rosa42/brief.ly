import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "@/app/AuthContext"


export function Header() {
    const { isLoggedIn } = useAuth();
	return (
    <header className="flex justify-between items-center px-6 py-4">
        <Link to="/" className="font-bold text-xl text-primary">Flagrant Daily</Link>
        {isLoggedIn ? <HeaderLogged /> : <HeaderUnlogged />}
    </header>
	)
}


export function HeaderLogged(){
    const { logout } = useAuth();
    const navigate = useNavigate();

    return (

        <div className="flex gap-4">
            <button type="submit" onClick={() => { logout(); navigate("/"); }} className="text-primary px-4 py-2 hover:text-secondary">Log out</button>
            <Link to="/profile" className="bg-primary text-background px-4 py-2 rounded hover:text-secondary">Profile</Link>
        </div>
    );
}

export function HeaderUnlogged(){
    return (
        <div className="flex gap-4">
            <Link to="/login" className="text-primary px-4 py-2 hover:text-secondary">Log in</Link>
            <Link to="/signup" className="bg-primary text-background px-4 py-2 rounded hover:text-secondary">Sign up</Link>
        </div>
    );

}