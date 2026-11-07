import { createContext } from "react";
import type { Profile } from "@/features/profile/api";

export interface ProfileContextValue {
	profile: Profile | null;
	isProfileComplete: boolean;
	setProfile: (profile: Profile | null) => void;
	loading: boolean;
	error: string | null;
	reload: () => Promise<void>;
}

export const ProfileContext = createContext<ProfileContextValue | undefined>(undefined);
