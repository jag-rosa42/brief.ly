// Exercice 4 — State & événements React
//
// Jusqu'ici, tes composants étaient "statiques" : ils affichaient juste ce
// qu'on leur donnait en props, sans jamais changer eux-mêmes. On introduit
// ici le state : une donnée interne au composant, qui peut changer dans le
// temps (un compteur, une case cochée, un texte tapé...).
//
// Contrairement à `var`, tu ne peux PAS juste déclarer une variable normale
// pour ça — React doit être informé qu'une donnée a changé pour réafficher
// le composant. C'est le rôle du hook `useState` :
//
//   const [value, setValue] = useState(initialValue);
//
// `value` est la valeur actuelle, `setValue` est LA SEULE façon de la
// changer. Appeler `setValue(x)` dit à React "cette donnée a changé,
// réaffiche le composant avec la nouvelle valeur". C'est un hook, donc
// (règle React) il s'appelle toujours au tout début du corps du composant,
// jamais dans une condition ou une boucle.
//
// Pour réagir à un événement, on passe une fonction à une prop spéciale
// sur un élément JSX : `onClick` pour un clic, `onChange` pour un input.
//
//   <button onClick={() => setValue(value + 1)}>+1</button>
//   <input onChange={(e) => setValue(e.target.value)} />
//
// Une fois codé, lance dans srcs/frontend/ : npm test

import { useState } from "react";

// 1. ToggleButton affiche un bouton dont le texte est "Show" au départ.
//    Chaque clic doit alterner le texte entre "Show" et "Hide".
//    Indice : useState(false), et au clic tu inverses la valeur.
export function ToggleButton() {
	return null; // TODO
}

// 2. Counter affiche "Count: 0" au départ, avec un bouton "+1" à côté.
//    Chaque clic sur le bouton doit incrémenter le nombre affiché.
export function Counter() {
	return null; // TODO
}

// 3. TextEcho affiche un <input> et, juste en dessous, un <p> qui répète
//    en direct ce que l'utilisateur tape dans l'input.
//    Indice : `onChange` te donne un événement `e`, et `e.target.value`
//    contient le texte actuel de l'input.
export function TextEcho() {
	return null; // TODO
}

// 4. ItemList prend une prop `initialItems` (string[]) et les affiche dans
//    une <ul>/<li> (comme ProductList à l'exercice 3). Ajoute un bouton
//    "Clear" qui vide la liste au clic. Quand la liste est vide, affiche
//    "No items" à la place de la <ul>.
//    Indice : le state démarre avec la valeur de la prop
//    (useState(props.initialItems)), puis évolue indépendamment d'elle.
export function ItemList(/* TODO */) {
	return null; // TODO
}

// 5. LikeButton affiche un bouton. Son texte est "Like" au départ, et
//    devient "Liked" après un clic — mais contrairement à ToggleButton,
//    ça ne revient jamais en arrière, même si on reclique.
export function LikeButton() {
	return null; // TODO
}
