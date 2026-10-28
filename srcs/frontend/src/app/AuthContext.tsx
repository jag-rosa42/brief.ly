import { useEffect, useState } from "react";
import type { ReactNode } from "react";

import { AuthContext } from "@/app/AuthContextDefinition";
import { register as apiRegister, logout as apiLogout, restoreSession, getMe } from "@/features/auth/identity";
import { type Account } from "@/features/auth/types"
import { session } from "@/shared/components/api/client";

interface AuthProviderProps {
	children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
	const [account, setAccount] = useState<Account | null>(null);
	const [isLoading, setIsLoading] = useState(true);

	//TODO: Temporaire : à remplacer quand le profil sera relié au backend.
	const [profileComplete, setProfileComplete] = useState(() => localStorage.getItem("profileComplete") === "true");

	const isLoggedIn = (account !== null);
	// TODO: Mock: a remplacer avec les donnees du back end
	function login() {
		localStorage.setItem("token", "fake-token");
		localStorage.setItem("profileComplete", "true");
		setAccount({
			id: "mock-user",
			email: "demo@example.com",
			created_at: new Date().toISOString(),
		});
		setProfileComplete(true);
	}

	useEffect(() => {
		let active = true;

		const unsubscribe = session.onExpired(() => {
			if (active) {
				setAccount(null);
			}
		});

		async function bootstrap() {
			try {
				const restored = await restoreSession();

				if (!active) return;

				if (restored) {
					const account = await getMe();

					if (!active)
						return;

					setAccount(account);

					// TODO: Restore profile completion status from the backend.
				} else {
					setAccount(null);
				}
			} catch {
				if (active) {
					setAccount(null);
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
			unsubscribe();
		};
	}, []);

	async function signup(email: string, password: string) {
		await apiRegister(email, password);
		const account = await getMe();

		setAccount(account);
		setProfileComplete(false);
		// TODO: Remove localStorage when profile completion is managed by the backend.
		localStorage.setItem("profileComplete", "false");
	}

	async function logout() {
		try {
			await apiLogout();
		} finally {
			setAccount(null);
			setProfileComplete(false);
			// TODO: Remove localStorage when profile completion is managed by the backend.
			localStorage.removeItem("profileComplete");
			sessionStorage.removeItem("lastPath");
		}
	}

	function completeProfile() {
		setProfileComplete(true);
		// TODO: Remove localStorage when profile completion is managed by the backend.
		localStorage.setItem("profileComplete", "true");
	}

	return (
		<AuthContext
			value={{
				account,
				isLoggedIn,
				isLoading,
				profileComplete,
				signup,
				login,
				completeProfile,
				logout,
			}}
		>
			{children}
		</AuthContext>
	);
}
