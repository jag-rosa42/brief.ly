import { createContext } from "react";
import type { Account } from "@/features/auth/types";

export interface AuthContextValue {
	account: Account | null;
	isLoggedIn: boolean;
	isLoading: boolean;
	profileComplete: boolean;
	signup: (email: string, password: string) => Promise<void>;
	completeProfile: () => void;
	login: () => void;
	logout: () => Promise<void>;
}

export const AuthContext = createContext<AuthContextValue | undefined>(
	undefined,
);