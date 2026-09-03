// EXERCICE 5 — REACT ROUTER : NAVIGATION ENTRE PAGES
//
//
// Dans une SPA (Single Page Application), il n'y a qu'une seule vraie page
// HTML. React Router intercepte les clics sur les liens internes et change
// juste quel composant s'affiche, sans recharger le navigateur — c'est ce
// qui te permet d'avoir une Landing page, une page "About Us", une page
// "Privacy"... comme des pages séparées, mais rapides et sans rechargement.
//
// Trois briques essentielles (du package `react-router-dom`) :
//
// - <Routes> / <Route path="..." element={<Comp />} /> : associe une URL
//   à un composant à afficher. `path="*"` sert de "route par défaut"
//   (catch-all) si aucune autre route ne matche — utile pour une page 404.
//
// - <Link to="/about">About</Link> : équivalent d'un <a href="/about">,
//   mais géré par React Router (pas de rechargement de page).
//
// - <BrowserRouter> : le composant qui doit envelopper TOUTE ton
//   application (normalement une seule fois, dans main.tsx) pour que
//   Routes/Link fonctionnent, en s'appuyant sur la vraie URL du
//   navigateur.
//
// Détail important pour les tests : on n'utilise JAMAIS <BrowserRouter>
// dans un test (pas de vrai navigateur). On utilise <MemoryRouter> à la
// place, qui simule une URL en mémoire — regarde exercise5.test.tsx.
// C'est pour ça que tes composants ci-dessous ne doivent PAS inclure de
// <BrowserRouter> eux-mêmes : seul `main.tsx` (le vrai point d'entrée de
// l'appli) devrait le faire, jamais un composant réutilisable/testable.
//
// Une fois codé, lance dans srcs/frontend/ : npm test

import { Link, Route, Routes } from "react-router-dom";

// 1. HomePage : un composant simple qui affiche un <h1>Home</h1>.
export function HomePage() {
	return null; // TODO
}

// 2. AboutPage : un composant simple qui affiche un <h1>About</h1>.
export function AboutPage() {
	return null; // TODO
}

// 3. NotFoundPage : un composant simple qui affiche un <h1>404</h1>.
//    (Ce sera la page affichée pour toute URL qui ne correspond à rien.)
export function NotFoundPage() {
	return null; // TODO
}

// 4. AppRoutes assemble tout :
//    - une <nav> avec deux <Link> : un vers "/" (texte "Home"),
//      un vers "/about" (texte "About")
//    - juste en dessous, un <Routes> avec 3 <Route> :
//      "/" -> HomePage, "/about" -> AboutPage, "*" -> NotFoundPage
export function AppRoutes() {
	return null; // TODO
}
