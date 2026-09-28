import { Link } from "@/shared/components/Link"
import { Button } from "@/shared/components/Button"


export function Header() {
	return (
    <header className="flex justify-between items-center px-6 py-4">
        <Link to="/" variant="title">Brief<span className="text-secondary">.ly</span></Link>
        {/* TODO: will display <NavbarLogged/> or <NavbarUnlogged/> depending on connection state*/}
        <NavbarUnlogged/>
    </header>
	)
}

export function NavbarLogged(){
    return (
        <div className="flex gap-4">
            <Button type="submit" variant="primary">Log out</Button>
            <Link to="/profile" variant="secondary">Profile</Link>
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
