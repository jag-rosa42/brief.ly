// EXERCICE 7 — FORMULAIRES, VALIDATION ET APPELS API ASYNCHRONES
//
//
// C'est l'exercice qui te donne tout ce qu'il manque avant d'attaquer le
// vrai formulaire d'inscription (ticket V-021) : soumettre un formulaire,
// valider plusieurs champs à la fois, et appeler une API en async avec les
// états loading/success/error.
//
// Soumettre un formulaire :
//   <form onSubmit={handleSubmit}>...</form>
// Par défaut, soumettre un <form> recharge la page (comportement du
// navigateur) — en React, tu veux presque toujours l'empêcher avec
// `e.preventDefault()`, en tout premier dans ton handler :
//   function handleSubmit(e: FormEvent) {
//     e.preventDefault();
//     ...
//   }
//
// Formulaire avec plusieurs champs contrôlés : un `useState` par champ
// (comme TextEcho à l'exercice 4), et un state en plus pour l'erreur de
// validation (string, "" = pas d'erreur) :
//   const [error, setError] = useState("");
//
// Appel API asynchrone : une fonction `async`, `await fetch(...)`, et un
// state "machine à états" pour savoir où on en est :
//   const [status, setStatus] = useState<"idle" | "loading" | "success" | "error">("idle");
//   async function handleSubmit(e: FormEvent) {
//     e.preventDefault();
//     if (!valide) { setError(...); return; }
//     setStatus("loading");
//     const response = await fetch("/api/register", {
//       method: "POST",
//       body: JSON.stringify({ email, password }),
//     });
//     setStatus(response.ok ? "success" : "error");
//   }
//
// Important pour les tests (regarde exercise7.test.tsx) : chaque input doit
// avoir un <label> associé (via htmlFor="id" + id="id" sur l'input, ou en
// mettant l'input à l'intérieur du <label>), sinon `getByLabelText` ne le
// trouve pas. Et un message d'erreur/alerte doit être dans un élément avec
// `role="alert"` pour que `getByRole("alert")` le trouve.
//
// Une fois codé, lance dans srcs/frontend/ : npm test

import { useState } from "react";
import type { FormEvent } from "react";

// 1. PasswordMatchForm affiche un <form> avec deux champs contrôlés :
//    "Password" et "Confirm password" (des <input type="password">, chacun
//    avec un <label> associé). Un bouton "Submit" en dessous.
//    Au submit (preventDefault) :
//    - si les deux valeurs sont différentes, affiche
//      <p role="alert">Passwords do not match</p>
//    - sinon, affiche <p>Passwords match</p>
//    Indice : un state `error` (string) suffit ; "" = pas d'erreur, dans ce
//    cas affiche le message de succès à la place.
export function PasswordMatchForm(/* TODO */) {
	return null; // TODO
}

// 2. EmailForm affiche un <form> avec un champ contrôlé "Email" (<input>
//    avec un <label>) et un bouton "Submit".
//    Au submit (preventDefault) : si la valeur ne contient pas "@", affiche
//    <p role="alert">Invalid email</p> ; sinon affiche <p>Email OK</p>.
export function EmailForm(/* TODO */) {
	return null; // TODO
}

// 3. SignupForm est le gros morceau, celui qui ressemble le plus au vrai
//    formulaire d'inscription. Trois champs contrôlés avec leurs <label> :
//    "Email", "Password", "Confirm password". Un bouton "Sign up".
//
//    Validation au submit (preventDefault), dans cet ordre — arrête-toi au
//    premier problème trouvé et affiche UN SEUL message dans
//    <p role="alert">...</p> :
//      - email vide ou sans "@"       -> "Invalid email"
//      - password vide                -> "Password is required"
//      - confirm password différent   -> "Passwords do not match"
//    Si tout est invalide, PAS d'appel à l'API.
//
//    Appel API : si la validation passe, passe en état "loading" (le
//    bouton "Sign up" doit devenir disabled tant qu'on attend), puis
//    `await fetch("/api/register", { method: "POST", body:
//    JSON.stringify({ email, password }) })`.
//    - si `response.ok` est true -> affiche <p>Registration successful</p>
//    - sinon -> affiche <p role="alert">Registration failed</p>
//    Indice : un state `status` ("idle" | "loading" | "success" | "error")
//    piloté comme dans l'exemple du header suffit pour tout ça.
export function SignupForm(/* TODO */) {
	return null; // TODO
}
