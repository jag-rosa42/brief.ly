import { useEffect, useState } from "react";
import type { ReactNode } from "react";

import { AuthContext } from "@/app/AuthContextDefinition";
import {
	register as apiRegister,
	login as apiLogin,
	logout as apiLogout,
	restoreSession,
	getMe,
} from "@/features/auth/identity";
import { type Account } from "@/features/auth/types";
import { session } from "@/shared/components/api/client";
import { LAST_PATH } from "@/app/navigation";

interface AuthProviderProps {
	children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
	const [account, setAccount] = useState<Account | null>(null);
	const [isLoading, setIsLoading] = useState(true);

	const isLoggedIn = account !== null;

	async function login(email: string, password: string) {
		await apiLogin(email, password);
		const account = await getMe();
		setAccount(account);
	}

	async function signup(email: string, password: string) {
		await apiRegister(email, password);
		const account = await getMe();
		setAccount(account);
	}

	async function logout() {
		try {
			await apiLogout();
		} finally {
			setAccount(null);
			sessionStorage.removeItem(LAST_PATH);
		}
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

					if (!active) return;

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

	return (
		<AuthContext
			value={{
				account,
				isLoggedIn,
				isLoading,
				signup,
				login,
				logout,
			}}
		>
			{children}
		</AuthContext>
	);
}
