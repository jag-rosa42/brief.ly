export const buttonVariants = ["primary", "secondary", "text", "title", "main"] as const;
export type ButtonVariant = typeof buttonVariants[number];

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
    variant: ButtonVariant;
}


export function getButtonStyle(style: string): string
{
    switch(style) {
        case "primary":
            return ("text-primary px-4 py-2 border-1 rounded-[999px] border-primary \
                hover:border-primary-dark hover:text-primary-dark");
        case "secondary":
            return("bg-primary text-background px-4 py-2 rounded-[999px] \
                hover:bg-primary-dark");
        case "text":
            return("font-serif text-accent-dark");
        case "title":
            return("font-bold text-xl text-primary");
        case "main":
            return("bg-accent-dark text-background px-5 py-2.5 rounded-[999px] hover:bg-accent");
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
