// EXERCICE 2 — TYPESCRIPT DE BASE
//
//
// TypeScript ajoute des types par-dessus JavaScript. Le code s'exécute
// toujours en JS (les types sont juste vérifiés puis effacés), mais ça te
// protège d'erreurs bêtes (passer un string là où on attend un number, etc.)
// et ça documente le code.
//
// `interface` et `type` servent tous les deux à décrire la forme d'un objet.
// On utilise `interface` ici pour les objets "métier" (Product, User...),
// et `type` pour les unions/alias (comme Status plus bas). C'est une
// convention, pas une règle stricte.

// 1. Complète l'interface Product : id (number), name (string),
//    price (number), et description qui est OPTIONNELLE (string).
//    Indice : une propriété optionnelle s'écrit avec un `?` avant le `:`.
export interface Product {
	// TODO: id (number), name (string), price (number), description? (string)
}

// 2. Écris une fonction qui prend un Product et retourne une string du
//    type "Coffee - $12.5". Utilise un template literal.
export function formatPrice(product: Product): string {
	// TODO
	return "";
}

// 3. Un "union type" liste les valeurs possibles autorisées, séparées
//    par des |. Complète le type Status avec les 3 états, puis écris
//    nextStatus qui fait passer au statut suivant dans l'ordre
//    pending -> active -> done -> pending (ça boucle).
export type Status = "pending" | "active" | "done"; // TODO: garde ces 3, ne change rien ici

export function nextStatus(status: Status): Status {
	// TODO
	return status;
}

// 4. Cette fonction doit accepter SOIT un number SOIT un string comme id,
//    et retourner toujours une string (ex: formatId(5) => "ID-5",
//    formatId("abc") => "ID-abc"). Type le paramètre `id` avec un union
//    type (number | string).
export function formatId(id: any): string {
	// TODO: remplace `any` par le bon union type
	return "";
}

// 5. Complète le tableau `products` ci-dessous avec au moins 3 objets
//    Product (certains avec description, d'autres sans, puisqu'elle est
//    optionnelle). Puis écris getExpensiveProducts qui retourne les
//    Product dont le price est >= minPrice.
export const products: Product[] = [
	// TODO: ajoute au moins 3 objets Product
];

export function getExpensiveProducts(
	products: Product[],
	minPrice: number
): Product[] {
	// TODO
	return [];
}
