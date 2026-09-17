import { Button, buttonVariants } from "@/shared/components/Button";
import { Link } from "@/shared/components/Link";
import { Text, textVariants } from "@/shared/components/Text";
import { Division, divVariants } from "@/shared/components/Division";


export function DesignSystem() {
    return (
        <div className="bg-gray-300 min-h-screen flex flex-col gap-4 p-4">
            <div className="flex gap-2">
                {buttonVariants.map((variant) => (
                    <Button key={variant} variant={variant}>
                        {variant} button
                    </Button>
                ))}
            </div>
            <div className="flex gap-2">
                {buttonVariants.map((variant) => (
                    <Link key={variant} to="/designsystem" variant={variant}>
                        {variant} link
                    </Link>
                ))}
            </div>
            <div className="flex flex-col gap-2">
                {textVariants.map((variant) => (
                    <Text key={variant} variant={variant}>
                        {variant} text
                    </Text>
                ))}
            </div>
            <div className="flex gap-4">
                {divVariants.map((variant) => (
                    <Division key={variant} variant={variant}>
                        {variant} division with some sample content inside to check the layout.
                    </Division>
                ))}
            </div>
        </div>
    );
}
