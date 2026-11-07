import { useCallback, useEffect, useMemo, useState } from "react";
import { ApiError } from "@/shared/components/api/client";
import {
	buildPayload,
	getTopics,
	upsertProfile,
	type Profile,
	type Topic,
} from "@/features/profile/api";
import { mapProfileError, validate, type FormErrors } from "@/features/profile/validation";
import { useProfile } from "@/app/useProfile";

export function useProfileForm() {
	// Le profil vient du contexte (chargé par ProfileProvider).
	const { profile, setProfile } = useProfile();

	const [topics, setTopics] = useState<Topic[]>([]);
	const [name, setName] = useState(profile?.name ?? "");
	const [topicIds, setTopicIds] = useState<string[]>(profile?.topic_ids ?? []);

	const [loading, setLoading] = useState(true);
	const [loadError, setLoadError] = useState<string | null>(null);
	const [submitting, setSubmitting] = useState(false);
	const [attempted, setAttempted] = useState(false);
	const [serverErrors, setServerErrors] = useState<FormErrors>({});
	const [success, setSuccess] = useState(false);

	const reload = useCallback(async () => {
		setLoading(true);
		setLoadError(null);
		try {
			setTopics(await getTopics());
		} catch (e) {
			if (e instanceof ApiError && e.status === 401) return;
			setLoadError("Unable to load interests.");
		} finally {
			setLoading(false);
		}
	}, []);

	// Au premier affichage de la page, on charge les topics.
	useEffect(() => {
		let ignore = false;

		void getTopics()
			.then((items) => {
				if (!ignore) setTopics(items);
			})
			.catch((e: unknown) => {
				if (ignore) return;
				if (e instanceof ApiError && e.status === 401) return;
				setLoadError("Unable to load interests.");
			})
			.finally(() => {
				if (!ignore) setLoading(false);
			});

		// Si le composant est démonté avant la réponse, on ignore le résultat.
		return () => {
			ignore = true;
		};
	}, []);

	const touch = () => {
		setSuccess(false);
		setServerErrors({});
	};

	const changeName = (value: string) => {
		touch();
		setName(value);
	};

	const toggleTopic = (id: string) => {
		touch();
		setTopicIds((prev) => {
			if (prev.includes(id)) {
				return prev.filter((topic) => topic !== id);
			}

			if (prev.length < 4) {
				return [...prev, id];
			}

			return prev;
		});
	};

	const clientErrors = useMemo(() => validate(name, topicIds), [name, topicIds]);
	const payload = useMemo(
		() => buildPayload(profile, { name, topicIds }),
		[profile, name, topicIds],
	);
	const isEmptyUpdate = profile !== null && Object.keys(payload).length === 0;

	// Les erreurs client ne s'affichent qu'après une première tentative.
	const errors: FormErrors = {};

	if (attempted) {
		if (clientErrors.name) {
			errors.name = clientErrors.name;
		}
		if (clientErrors.topics) {
			errors.topics = clientErrors.topics;
		}
	}
	if (serverErrors.name) {
		errors.name = serverErrors.name;
	}
	if (serverErrors.topics) {
		errors.topics = serverErrors.topics;
	}
	if (serverErrors.form) {
		errors.form = serverErrors.form;
	}

	const submit = async (): Promise<Profile | null> => {
		if (submitting) return null;
		setAttempted(true);
		if (clientErrors.name || clientErrors.topics) return null;
		if (isEmptyUpdate) return null; // No changes to submit: prevent sending an empty PUT request (which would return 422).

		setSubmitting(true);
		setServerErrors({});
		setSuccess(false);
		try {
			const saved = await upsertProfile(payload);
			setProfile(saved);
			setName(saved.name);
			setTopicIds(saved.topic_ids);
			setSuccess(true);
			return saved;
		} catch (e) {
			if (e instanceof ApiError && e.status === 401) return null;
			setServerErrors(mapProfileError(e));
			return null;
		} finally {
			setSubmitting(false);
		}
	};

	return {
		mode: profile ? ("update" as const) : ("create" as const),
		topics,
		name,
		setName: changeName,
		topicIds,
		toggleTopic,
		loading,
		loadError,
		reload,
		submitting,
		success,
		errors,
		submit,
		canSubmit: !submitting && !loading && !loadError && !isEmptyUpdate,
	};
}
