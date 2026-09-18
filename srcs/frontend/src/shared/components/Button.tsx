export const buttonVariants = ["primary", "secondary", "text", "title"] as const;
export type ButtonVariant = typeof buttonVariants[number];

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
    variant: ButtonVariant;
}


export function getButtonStyle(style: ButtonVariant): string
{
    switch(style) {
        case "primary":
            return ("text-primary px-4 py-2 border-1 rounded border-primary \
                hover:border-primary-dark hover:text-primary-dark");
        case "secondary":
            return("bg-primary text-background px-4 py-2 rounded \
                hover:bg-primary-dark");
        case "text":
            return("text-background");
        case "title":
            return("font-bold text-xl text-primary");
        default:
        return("") ;
    }
}

export function Button({
    variant,
    children,
    className,
    ...props
}: ButtonProps) {
    const style = getButtonStyle(variant);

    return (
        <button
            {...props}
            className={`${style} ${className ?? ""}`}
        >
            {children}
        </button>
    );
}
