import { Button, buttonVariants } from "@/shared/components/Button";
import { Link } from "@/shared/components/Link";


export function DesignSystem() {
    return (
        <div className="bg-gray-300 min-h-screen flex flex-col gap-4">
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
        </div>
    );
}
