import { createContext } from "react";
import type { Account } from "@/features/auth/types";

export interface AuthContextValue {
	account: Account | null;
	isLoggedIn: boolean;
	isLoading: boolean;
	signup: (email: string, password: string) => Promise<void>;
	login: (email: string, password: string) => Promise<void>;
	logout: () => Promise<void>;
}

export const AuthContext = createContext<AuthContextValue | undefined>(undefined);
