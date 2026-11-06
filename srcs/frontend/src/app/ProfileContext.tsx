import { useCallback, useEffect, useState } from "react";
import type { ReactNode } from "react";

import { ProfileContext } from "@/app/ProfileContextDefinition";
import { useAuth } from "@/app/useAuth";
import { ApiError } from "@/shared/components/api/client";
import { getProfile, type Profile } from "@/features/profile/api";

interface ProfileProviderProps {
	children: ReactNode;
}

export function ProfileProvider({ children }: ProfileProviderProps) {
	const { isLoggedIn, isLoading: authLoading } = useAuth();
	const [profile, setProfile] = useState<Profile | null>(null);
	const [loaded, setLoaded] = useState(false);
	const [error, setError] = useState<string | null>(null);

	const reload = useCallback(async () => {
		setLoaded(false);
		setError(null);
		try {
			setProfile(await getProfile()); // null si PROFILE_NOT_FOUND
		} catch (e) {
			if (e instanceof ApiError && e.status === 401) return;
			setError(e instanceof Error ? e.message : "Unable to load profile.");
		} finally {
			setLoaded(true);
		}
	}, []);

	const [wasLoggedIn, setWasLoggedIn] = useState(isLoggedIn);
	if (wasLoggedIn !== isLoggedIn) {
		setWasLoggedIn(isLoggedIn);
		if (!isLoggedIn) {
			setProfile(null);
			setLoaded(false);
			setError(null);
		}
	}

	// Quand l'utilisateur est connecté, on charge son profil.
	useEffect(() => {
		if (authLoading || !isLoggedIn) return;

		let ignore = false;

		void getProfile()
			.then((loadedProfile) => {
				if (!ignore) setProfile(loadedProfile); // null si PROFILE_NOT_FOUND
			})
			.catch((e: unknown) => {
				if (ignore) return;
				if (e instanceof ApiError && e.status === 401) return;
				setError(e instanceof Error ? e.message : "Unable to load profile.");
			})
			.finally(() => {
				if (!ignore) setLoaded(true);
			});

		// Si l'effet est relancé ou le composant démonté, on ignore la réponse en cours.
		return () => {
			ignore = true;
		};
	}, [authLoading, isLoggedIn]);

	const loading = authLoading || (isLoggedIn && !loaded);

	return (
		<ProfileContext value={{ profile, setProfile, loading, error, reload }}>
			{children}
		</ProfileContext>
	);
}
