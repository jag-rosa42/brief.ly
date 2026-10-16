import { createContext } from "react";

export interface AuthContextValue {
	isLoggedIn: boolean;
	profileComplete: boolean;
	login: () => void;
	signup: (email: string, password: string) => Promise<void>;
	completeProfile: () => void;
	logout: () => void;
}

export const AuthContext = createContext<AuthContextValue | undefined>(
	undefined,
);