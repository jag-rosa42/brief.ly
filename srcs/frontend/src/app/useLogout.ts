import { useNavigate } from "react-router-dom";
import { useAuth } from "@/app/useAuth";
import { useNotify } from "@/app/useNotify";

export function useLogout() {
	const navigate = useNavigate();
	const { logout } = useAuth();
	const { notify } = useNotify();

	async function handleLogout() {
		await logout();
		notify("You have been logged out.", "info");
		void navigate("/");
	}

	return handleLogout;
}
