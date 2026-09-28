import { Button, buttonVariants } from "@/shared/components/Button";
import { Link } from "@/shared/components/Link";
import { Text, textVariants } from "@/shared/components/Text";
import { Division, divVariants } from "@/shared/components/Division";
import { Card } from "@/shared/components/Card"

const article = {
    title: "Les LLM en 2026 : où en est-on",
    description:
        "Un tour d'horizon des avancées récentes en matière de modèles de langage et leurs limites actuelles.",
};

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
            <h2 className="text-lg font-bold">Card</h2>
            <section>
                <Card
                    title={article.title}
                    description={article.description}
                    className="w-full max-w-sm"
                />
            </section>
        </div>
    );
}
