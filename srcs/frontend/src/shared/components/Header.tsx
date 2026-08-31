import { Link } from "react-router-dom";
export function Header() {
	return (
    <header className="flex justify-between items-center px-6 py-4">
        <Link to="/" className="font-bold text-xl text-primary">Flagrant Daily</Link>
        <div className="flex gap-4">
            <Link to="/login" className="text-primary px-4 py-2 hover:text-secondary">Log in</Link>
            <Link to="/signup" className="bg-primary text-background px-4 py-2 rounded hover:text-secondary">Sign up</Link>
        </div>
    </header>
	)
}