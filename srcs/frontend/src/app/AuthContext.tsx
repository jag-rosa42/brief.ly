import { createContext, useContext, useState } from "react";
import type { ReactNode } from "react";

interface AuthContextValue {
	isLoggedIn: boolean;
	login: () => void;
	logout: () => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

interface AuthProviderProps {
	children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
	const [isLoggedIn, setIsLoggedIn] = useState(() => !!localStorage.getItem("token"));

	function login() {
		localStorage.setItem("token", "fake-token");
		setIsLoggedIn(true);
	}

	function logout() {
		localStorage.removeItem("token");
		setIsLoggedIn(false);
	}

	return (
		<AuthContext.Provider value={{ isLoggedIn, login, logout }}>
			{children}
		</AuthContext.Provider>
	);
}

export function useAuth() {
	const context = useContext(AuthContext);
	if (context === undefined) {
		throw new Error("useAuth must be used within an AuthProvider");
	}
	return context;
}
