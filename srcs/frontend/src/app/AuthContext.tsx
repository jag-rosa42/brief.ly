import { createContext, useContext, useState } from "react";
import type { ReactNode } from "react";

interface AuthContextValue {
	isLoggedIn: boolean;
	profileComplete: boolean;
	login: () => void;
	signup: () => void;
	completeProfile: () => void;
	logout: () => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

interface AuthProviderProps {
	children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
	const [isLoggedIn, setIsLoggedIn] = useState(() => !!localStorage.getItem("token"));
	const [profileComplete, setProfileComplete] = useState(
		() => localStorage.getItem("profileComplete") === "true"
	);

	function login() {
		localStorage.setItem("token", "fake-token");
		localStorage.setItem("profileComplete", "true");
		setIsLoggedIn(true);
		setProfileComplete(true);
	}

	function signup() {
		localStorage.setItem("token", "fake-token");
		localStorage.setItem("profileComplete", "false");
		setIsLoggedIn(true);
		setProfileComplete(false);
  	}

  	function completeProfile() {
		localStorage.setItem("profileComplete", "true");
		setProfileComplete(true);
  	}
	function logout() {
		localStorage.removeItem("token");
		localStorage.setItem("profileComplete", "true");
		setIsLoggedIn(false);
		setProfileComplete(false);
	}

	return (
		<AuthContext.Provider value={{ isLoggedIn, profileComplete, login, signup, completeProfile, logout }}>
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
