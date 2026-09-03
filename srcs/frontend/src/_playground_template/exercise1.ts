// EXERCICE 1 — JAVASCRIPT MODERNE (ES6+)
//
//
// Complète chaque fonction ci-dessous. Ignore la syntaxe `: number[]` etc.
// pour l'instant (c'est du TypeScript, on l'expliquera à l'exercice 2) —
// contente-toi de lire ça comme "cette fonction prend un tableau de nombres
// et retourne un nombre".
//
// Une fois que tu as codé, lance dans srcs/frontend/ : npm test
// Les tests dans exercise1.test.ts te diront si c'est bon.

// 1. Utilise .reduce() (ou une boucle si tu préfères, mais essaie reduce)
//    pour additionner tous les nombres d'un tableau.
export function sumArray(numbers: number[]): number {
	// TODO
	return 0;
}

// 2. Utilise .map() pour retourner un nouveau tableau où chaque nombre
//    est multiplié par 2.
export function doubleAll(numbers: number[]): number[] {
	// TODO
	return [];
}

// 3. Utilise .filter() puis .map() pour ne garder que les noms des
//    personnes majeures (age >= 18). Essaie de déstructurer { name, age }
//    directement dans les paramètres de la fonction fléchée que tu passes
//    à filter/map.
type Person = { name: string; age: number };

export function getAdultNames(people: Person[]): string[] {
	// TODO
	return [];
}

// 4. Écris une fonction fléchée (arrow function) avec un paramètre par
//    défaut pour `greeting`, et utilise un template literal pour
//    construire le message.
//    greet("Alice") => "Hello, Alice!"
//    greet("Bob", "Salut") => "Salut, Bob!"
export const greet = (name: string, greeting: string = "Hello"): string => {
	// TODO
	return "";
};

// 5. Utilise le spread operator (...) pour fusionner deux objets.
//    Si une clé existe dans les deux, la valeur de `overrides` doit gagner.
export function mergeSettings(
	defaults: Record<string, unknown>,
	overrides: Record<string, unknown>
): Record<string, unknown> {
	// TODO
	return {};
}
