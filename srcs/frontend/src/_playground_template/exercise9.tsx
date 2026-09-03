// EXERCICE 9 — CHOISIR DYNAMIQUEMENT UNE BALISE HTML
//
//
// Contexte : sur la vraie page Privacy Policy, tu as plusieurs blocs qui se
// répètent (un titre + un texte), mais avec des niveaux de titre différents
// (h1 pour le titre principal, h2 pour les sous-sections). Un reviewer a
// suggéré un composant <Heading level={1}> qui choisit LUI-MÊME quelle
// balise rendre (<h1>, <h2>, <h3>...) selon une prop.
//
// Jusqu'ici, tu choisissais une className différente selon une condition
// (Alert à l'exercice 6, ThemedButton à l'exercice 8). Ici, c'est le NOM DE
// LA BALISE elle-même qui doit changer — et ça ne s'écrit pas pareil.
//
// Tu ne peux PAS faire ceci (ce n'est pas du JSX valide) :
//   const tagName = "h" + level;
//   return <tagName>{children}</tagName>;   // ❌ rend littéralement <tagname>
//
// En JSX, une balise en minuscule (<div>, <p>...) est TOUJOURS interprétée
// comme une balise HTML littérale, jamais comme une variable — même si une
// variable du même nom existe. Pour utiliser une variable comme balise, elle
// doit commencer par une MAJUSCULE :
//   const Tag = condition ? "h1" : "h2";
//   return <Tag>{children}</Tag>;   // ✅ Tag commence par une majuscule,
//                                   //    React va chercher la VALEUR de la
//                                   //    variable ("h1" ou "h2") et l'utiliser
//                                   //    comme nom de balise.
//
// Ça marche parce qu'une balise HTML valide (h1, div, p...) est juste une
// STRING pour React — la variable `Tag` peut contenir n'importe laquelle de
// ces strings, et React s'en sert pour savoir quoi rendre.
//
// Une fois codé, lance dans srcs/frontend/ : npm test

import type { ReactNode } from "react";

// 1. Heading affiche `children` dans un titre dont le NIVEAU (h1, h2 ou h3)
//    dépend de la prop `level` (1 | 2 | 3).
//    Indice : construis une variable (commençant par une majuscule !) dont
//    la valeur est "h1", "h2" ou "h3" selon `level`, comme dans l'exemple
//    ci-dessus, puis utilise-la comme balise.
interface HeadingProps {
	level: 1 | 2 | 3;
	children: ReactNode;
}
export function Heading(/* TODO */) {
	return null; // TODO
}

// 2. Text affiche `children` dans un <p>, stylisé de façon cohérente avec
//    le reste du projet (regarde AboutPage.tsx ou PrivacyPolicyPage.tsx
//    pour t'inspirer d'une classe déjà utilisée sur un <p>).
interface TextProps {
	children: ReactNode;
}
export function Text(/* TODO */) {
	return null; // TODO
}

// 3. Section compose les deux composants précédents : elle affiche un
//    <section> contenant un <Heading level={2}>{title}</Heading> suivi de
//    <Text>{children}</Text>.
//    C'est exactement le pattern que tu utilises pour Layout (exercice V-01)
//    ou Badge : un composant qui n'affiche pas de contenu à lui, juste de la
//    structure autour d'autres composants.
interface SectionProps {
	title: string;
	children: ReactNode;
}
export function Section(/* TODO */) {
	return null; // TODO
}
