import { Button, buttonVariants } from "@/shared/components/Button";
import { Link } from "@/shared/components/Link";
import { Text, textVariants } from "@/shared/components/Text";
import { Division, divVariants } from "@/shared/components/Division";
import { Header } from "@/shared/components/Header";
import { Card } from "@/shared/components/Card"

const interests = [
    {
        interestTitle: "Intelligence artificielle",
        articles: [
            {
                title: "Les LLM en 2026 : où en est-on",
                description:
                    "Un tour d'horizon des avancées récentes en matière de modèles de langage et leurs limites actuelles.",
            },
            {
                title: "Apprentissage par renforcement expliqué",
                description:
                    "Comment les agents apprennent à prendre des décisions par essais et erreurs.",
            },
            {
                title: "Vers une IA plus sobre",
                description:
                    "Les efforts de l'industrie pour réduire le coût énergétique des modèles.",
            },
        ],
    },
];

export function DesignSystem() {
    return (
        <div className="bg-gray-300 min-h-screen flex flex-col gap-4 p-4">
            <h2 className="text-lg font-bold">Button</h2>
            <div className="flex gap-2">
                {buttonVariants.map((variant) => (
                    <Button key={variant} variant={variant}>
                        {variant} button
                    </Button>
                ))}
            </div>
            <h2 className="text-lg font-bold">Link</h2>
            <div className="flex gap-2">
                {buttonVariants.map((variant) => (
                    <Link key={variant} to="/designsystem" variant={variant}>
                        {variant} link
                    </Link>
                ))}
            </div>
            <h2 className="text-lg font-bold">Text</h2>
            <div className="flex flex-col gap-2">
                {textVariants.map((variant) => (
                    <Text key={variant} variant={variant}>
                        {variant} text
                    </Text>
                ))}
            </div>
            <h2 className="text-lg font-bold">Division</h2>
            <div className="flex gap-4">
                {divVariants.map((variant) => (
                    <Division key={variant} variant={variant}>
                        {variant} division with some sample content inside to check the layout.
                    </Division>
                ))}
            </div>
            <h2 className="text-lg font-bold">Header</h2>
            <div className="flex flex-col gap-2 bg-background">
                <Header />
            </div>
        
            <section>
                <div className="flex flex-col gap-8">
                    {interests.map((interest) => (
                        <div key={interest.interestTitle}>
                            <h3 className="mb-3 text-lg font-medium">
                                {interest.interestTitle}
                            </h3>

                            <div className="flex flex-wrap gap-4">
                                {interest.articles.map((article) => (
                                    <Card
                                        key={article.title}
                                        title={article.title}
                                        description={article.description}
                                        className="w-full max-w-sm"
                                        />
                                ))}
                            </div>
                        </div>
                    ))}
                    </div>
                </section>
            </div>
    );
}
