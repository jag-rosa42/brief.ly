import { createContext } from "react";
import type { Account } from "@/features/auth/identity";

export interface AuthContextValue {
	user: Account | null;
	isLoggedIn: boolean;
	isLoading: boolean;
	profileComplete: boolean;
	login: (email: string, password: string) => Promise<void>;
	signup: (email: string, password: string) => Promise<void>;
	completeProfile: () => void;
	logout: () =>  Promise<void>;
}

export const AuthContext = createContext<AuthContextValue | undefined>(
	undefined,
);