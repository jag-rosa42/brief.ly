// EXERCICE 8 — TAILWIND AVANCÉ : THÈME DU PROJET & RESPONSIVE
//
//
// L'exercice 6 t'a fait pratiquer Tailwind avec la palette générique
// (bg-blue-600, text-gray-600...). Mais le vrai projet a son propre thème,
// défini dans src/index.css :
//   --color-primary: #16a34a;    (vert)
//   --color-secondary: #0f766e;  (teal)
//   --color-accent: grey;
//   --color-background: white;
// Tailwind v4 génère automatiquement les classes utilitaires correspondantes :
// bg-primary, text-primary, border-primary, bg-secondary, text-accent, etc.
// Regarde shared/components/Header.tsx pour des exemples réels déjà dans le
// code : bg-primary, text-background, hover:text-secondary.
//
// Nouveauté de cet exercice : le responsive. Une classe Tailwind normale
// s'applique à toutes les tailles d'écran. En préfixant une classe avec un
// "breakpoint" (sm:, md:, lg:...), elle ne s'applique qu'à partir de cette
// largeur d'écran :
//   className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-6"
// -> 1 colonne par défaut (mobile), 2 colonnes à partir de "sm" (640px),
//    3 colonnes à partir de "md" (768px).
//
// Comme pour l'exercice 6, le rendu VISUEL ne se vérifie pas bien par un
// test automatique — lance `npm run dev` dans srcs/frontend/ et regarde le
// résultat dans le navigateur en plus de lancer `npm test`.
//
// Une fois codé, lance dans srcs/frontend/ : npm test (et npm run dev pour
// le rendu visuel)

import type { ReactNode } from "react";

// 1. ThemedButton affiche son `children` dans un <button>, avec une prop
//    `variant` ("primary" | "outline") qui change le style :
//    - "primary"  -> fond bg-primary, texte text-background
//    - "outline"  -> pas de fond, bordure border border-primary,
//                    texte text-primary
//    Dans les deux cas : padding, coins arrondis, et un effet au survol
//    (hover:) cohérent avec ce que tu vois dans Header.tsx.
//    Indice : comme Alert à l'exercice 6, choisis la bonne string de
//    classe selon `variant` avec un if/else.
interface ThemedButtonProps {
	variant: "primary" | "outline";
	children: ReactNode;
}
export function ThemedButton(/* TODO */) {
	return null; // TODO
}

// 2. FormField affiche un <label> associé à un <input> contrôlé (même
//    pattern que l'exercice 7 : props `label`, `value`, `onChange`).
//    Stylise l'input : bordure, padding, coins arrondis, largeur pleine
//    (w-full), et un style au focus (focus:) qui met en valeur le champ
//    (ex: focus:outline-none focus:border-primary ou focus:ring).
//    Le <label> doit être au-dessus de l'input (flex-col), avec un petit
//    espace entre les deux.
interface FormFieldProps {
	label: string;
	value: string;
	onChange: (value: string) => void;
}
export function FormField(/* TODO */) {
	return null; // TODO
}

// 3. CardGrid affiche son `children` dans un conteneur en grille
//    responsive : 1 colonne par défaut, 2 colonnes à partir de "sm",
//    3 colonnes à partir de "md", avec un espacement (gap) entre les
//    cartes.
interface CardGridProps {
	children: ReactNode;
}
export function CardGrid(/* TODO */) {
	return null; // TODO
}
