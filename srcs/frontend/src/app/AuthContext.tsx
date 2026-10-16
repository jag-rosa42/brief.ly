import { useState } from "react";
import type { ReactNode } from "react";
import { AuthContext } from "@/app/AuthContextDefinition";

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

	function signup(email: string, password: string): Promise<void> {
		// Mock : les identifiants seront utilisés lors de l'intégration API.
        void email;
        void password;

		localStorage.setItem("token", "fake-token");
		localStorage.setItem("profileComplete", "false");
		setIsLoggedIn(true);
		setProfileComplete(false);

		return Promise.resolve();
  	}

  	function completeProfile() {
		localStorage.setItem("profileComplete", "true");
		setProfileComplete(true);
  	}
	function logout() {
		localStorage.removeItem("token");
		localStorage.removeItem("profileComplete");
		setIsLoggedIn(false);
		setProfileComplete(false);
	}

	return (
		<AuthContext value={{ isLoggedIn, profileComplete, login, signup, completeProfile, logout }}>
			{children}
		</AuthContext>
	);
}

