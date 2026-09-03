// EXERCICE 6 — TAILWIND CSS
//
//
// Tailwind n'a pas de fichier .css séparé par composant : tu stylises
// directement en JSX, via la prop `className`, avec des classes utilitaires
// toutes faites (une classe = une règle CSS, en général). Le fichier
// src/index.css (déjà branché dans main.tsx) et vite.config.ts sont déjà
// configurés — tu n'as rien à toucher côté config.
//
// Quelques classes courantes pour démarrer :
// - Espacement : p-4 (padding), px-4/py-2 (horizontal/vertical), m-2, gap-4
// - Couleurs : bg-blue-600, text-white, border-gray-300 (échelle 50→950)
// - Forme : rounded, rounded-lg, shadow, shadow-md, border
// - Layout : flex, flex-col, items-center, justify-between
// - États : hover:bg-blue-700, focus:outline-none (préfixe + classe)
//
// Contrairement aux exercices précédents, le rendu VISUEL ne se vérifie
// pas bien par un test automatique — lance `npm run dev` dans
// srcs/frontend/ et regarde le résultat dans le navigateur en plus de
// lancer `npm test`.
//
// Une fois codé, lance dans srcs/frontend/ : npm test (et npm run dev
// pour le rendu visuel)

// 1. Card affiche un <div> "carte" avec un <h2>{title}</h2> et un
//    <p>{description}</p> à l'intérieur. Stylise-le comme une vraie carte :
//    fond blanc, padding, coins arrondis, une ombre légère.
//    (Le test ne vérifie que le texte, le style est à juger dans le
//    navigateur.)
export function Card(/* TODO */) {
	return null; // TODO
}

// 2. Alert prend une prop `type` ("success" | "error") et une prop
//    `message` (string), et affiche un <div role="alert">{message}</div>.
//    La couleur de fond doit changer selon `type` :
//    "success" -> une teinte de vert (ex: bg-green-100),
//    "error" -> une teinte de rouge (ex: bg-red-100).
//    Indice : comme pour nextStatus (exercice 2), tu peux tester `type`
//    avec un if/else et choisir la bonne string de classe en conséquence,
//    puis la passer à `className`.
export function Alert(/* TODO */) {
	return null; // TODO
}

// 3. PrimaryButton affiche son `children` dans un <button>, stylisé comme
//    un vrai bouton d'action : fond coloré, texte blanc, padding, coins
//    arrondis, et un effet au survol (hover:) qui assombrit légèrement le
//    fond. Pas de test sur le style ici non plus — à toi de juger dans le
//    navigateur si "ça a l'air cliquable".
export function PrimaryButton(/* TODO */) {
	return null; // TODO
}
