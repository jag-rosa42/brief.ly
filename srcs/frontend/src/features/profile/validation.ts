import { ApiError } from "@/shared/components/api/client";

export interface FormErrors {
	name?: string;
	topics?: string;
	form?: string;
}

const NAME_MIN = 1;
const NAME_MAX = 50;

export function validate(name: string, topicIds: string[]): FormErrors {
	const errors: FormErrors = {};
	const len = name.trim().length;

	if (len < NAME_MIN) errors.name = `Name must be at least ${NAME_MIN} characters.`;
	else if (len > NAME_MAX) errors.name = `Name must be at most ${NAME_MAX} characters.`;
	if (topicIds.length < 1 || topicIds.length > 4) errors.topics = "Pick between 1 and 4 interests.";
	return errors;
}

// Traduit une ApiError en erreurs par champ.
export function mapProfileError(err: unknown): FormErrors {
	// Cas 0 : ce n'est pas une ApiError (coupure réseau, TypeError...) : message générique.
	if (!(err instanceof ApiError)) {
		return { form: "Unable to reach the server. Check your connection and try again." };
	}
	// Cas 1 : le service est indisponible, on affiche un message général.
	if (err.status === 502 || err.status === 503 || err.status === 504) {
		return { form: "Service temporarily unavailable. Please try again later." };
	}
	// Cas 2 : le back a refusé les données (validation).
	if (err.status === 422) {
		const errors: FormErrors = {};
		// err.details peut être absent (undefined) : dans ce cas on prend une liste vide.
		const details = err.details ?? [];
		// Le back peut renvoyer plusieurs erreurs : on les traite une par une.
		for (const detail of details) {
			const fieldName = detail.field.toLowerCase();
			const message = detail.message;

			if (fieldName.includes("topic")) {
				// Si une erreur topics existe déjà, on ajoute la nouvelle à la suite.
				if (errors.topics) {
					errors.topics = `${errors.topics} ${message}`;
				} else {
					errors.topics = message;
				}
			} else if (fieldName.includes("name")) {
				errors.name = message;
			} else {
				// Champ inconnu : on l'affiche en message général.
				errors.form = message;
			}
		}
		// Si aucune erreur n'a pu être associée, on affiche le message global de l'erreur.
		const noErrorFound = !errors.name && !errors.topics && !errors.form;
		if (noErrorFound) {
			errors.form = "Some information is invalid. Please check your entries and try again.";
		}
		return errors;
	}
	// Cas 3 : toute autre erreur (réseau, 500...) : message général.
	return { form: "Unable to save your profile. Please try again." };
}
