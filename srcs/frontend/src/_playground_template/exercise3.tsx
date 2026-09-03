// EXERCICE 3 — COMPOSANTS REACT & PROPS
//
//
// Un composant React, c'est juste une fonction qui prend des "props"
// (un objet) et retourne du JSX (qui ressemble à du HTML mais c'est du
// JS transformé). React se charge de l'affichage réel.
//
// Contrairement à exercice1/exercice2, écris ces composants avec des
// `return (...)` classiques (pas besoin de boucles ici, le JSX remplace
// souvent tes boucles habituelles) — mais code comme tu le sens, les tests
// diront si ça marche.
//
// Une fois codé, lance dans srcs/frontend/ : npm test

// 1. Composant le plus simple possible : Greeting affiche "Hello, <name>!"
//    dans une balise <p>. La prop `name` est un string obligatoire.
//    Indice : type les props avec une interface, ex GreetingProps.
export function Greeting(/* TODO */) {
	return null; // TODO
}

// 2. Counter affiche la valeur reçue dans une prop `count` (number),
//    à l'intérieur d'un <span>, sous la forme "Count: 3".
export function Counter(/* TODO */) {
	return null; // TODO
}

// 3. UserCard prend un objet `user` en prop avec { name: string; email: string }
//    et affiche le nom dans un <h2> et l'email dans un <p>.
//    Indice : réutilise le pattern interface pour typer `user`.
export function UserCard(/* TODO */) {
	return null; // TODO
}

// 4. ProductList prend une prop `products` (tableau d'objets
//    { id: number; name: string }) et affiche une <ul> avec un <li> par
//    produit. Chaque <li> doit avoir une prop spéciale `key={product.id}`
//    (React en a besoin pour les listes — cherche pourquoi si tu veux,
//    mais retiens juste que c'est obligatoire).
export function ProductList(/* TODO */) {
	return null; // TODO
}

// 5. Badge affiche son enfant (children) entouré d'un <span>. C'est le
//    pattern le plus courant en React : un composant "wrapper" qui
//    n'a pas besoin de connaître le contenu qu'il affiche.
//    Utilisation attendue : <Badge>New</Badge> => <span>New</span>
//    Indice : la prop spéciale s'appelle `children`.
export function Badge(/* TODO */) {
	return null; // TODO
}
