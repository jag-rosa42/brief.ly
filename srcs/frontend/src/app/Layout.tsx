// Layout — enveloppe TOUTES les pages publiques pour leur donner un
// Footer commun, sans que chaque page ait à l'importer elle-même.
// C'est exactement le pattern `children` de Badge (exercice 3) : un
// composant qui affiche ce qu'on lui passe, entouré de son propre habillage.
//
// Utilisation prévue (voir app/router.tsx) :
//   <Layout><LandingPage /></Layout>
//
// À faire :
// - Affiche `children` (le contenu de la page), puis en dessous le
//   composant <Footer /> (shared/components/Footer).
import type { ReactNode } from "react";
import { Footer } from "../shared/components/Footer";
import { Header } from "../shared/components/Header";

interface LayoutProps {
	children: ReactNode;
}

export function Layout(props: LayoutProps) {
	return (
		<div className="bg-background min-h-screen">
			<Header />
			{props.children}
			<Footer />
		</div>
	);
}
