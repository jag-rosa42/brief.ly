import { useEffect, useState } from "react";
import type { ReactNode } from "react";

import { AuthContext } from "@/app/AuthContextDefinition";
import { login as apiLogin, register as apiRegister, logout as apiLogout, restoreSession, getMe, type Account } from "@/features/auth/identity";
import { onSessionExpired } from "@/shared/components/api/client";

interface AuthProviderProps {
	children: ReactNode;
}

export function AuthProvider({ children }:AuthProviderProps ) {
	const [user, setUser] = useState<Account | null>(null);
	const [isLoggedIn, setIsLoggedIn] = useState(false);
	const [isLoading, setIsLoading] = useState(true);

	// Temporaire : à remplacer quand le profil sera relié au backend.
	const [profileComplete, setProfileComplete] = useState(() => localStorage.getItem("profileComplete") === "true");

	useEffect(() => {
		let active = true;

		onSessionExpired(() => {
			if (active) {
				setUser(null);
				setIsLoggedIn(false);
			}
		});

		async function bootstrap() {
			try {
				const restored = await restoreSession();

				if (!active) return;

				if (restored) {
					const account = await getMe();

					if (!active) return;

					setUser(account);
					setIsLoggedIn(true);
				} else {
					setUser(null);
					setIsLoggedIn(false);
				}
			} catch {
				if (active) {
					setUser(null);
					setIsLoggedIn(false);
				}
			} finally {
				if (active) {
					setIsLoading(false);
				}
			}
		}

		void bootstrap();

		return () => {
			active = false;
			onSessionExpired(null);
		};
	}, []);

	async function login(email: string, password: string) {
		await apiLogin(email, password);
		try {
			const account = await getMe();
			setUser(account);
			setIsLoggedIn(true);
		} catch (e) {
			await apiLogout().catch(() => {});
			setUser(null);
			setIsLoggedIn(false);
			throw e;
		}
	}

	async function signup(email: string, password: string) {
		await apiRegister(email, password);
		const account = await getMe();

		setUser(account);
		setIsLoggedIn(true);
		setProfileComplete(false);
	}

	async function logout() {
		try {
			await apiLogout();
		} finally {
			setUser(null);
			setIsLoggedIn(false);
			setProfileComplete(false);
		}
	}

	function completeProfile() {
		setProfileComplete(true);
	}

	return (
		<AuthContext
			value={{
				user,
				isLoggedIn,
				isLoading,
				profileComplete,
				login,
				signup,
				completeProfile,
				logout,
			}}
		>
			{children}
		</AuthContext>
	);
}
