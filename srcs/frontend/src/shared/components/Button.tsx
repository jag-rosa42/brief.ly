export const buttonVariants = ["primary", "secondary", "simple", "title", "main", "link", "chip"] as const;
export type ButtonVariant = typeof buttonVariants[number];

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
    variant: ButtonVariant;
    selected?: boolean;
}

export function getButtonStyle(style: ButtonVariant, selected= false): string
{
    switch(style) {
        case "primary":
            return ("text-primary px-4 py-2 border-1 rounded-[999px] border-primary \
                hover:border-primary-dark hover:text-primary-dark");
        case "secondary":
            return("bg-primary text-background px-4 py-2 rounded-[999px] \
                hover:bg-primary-dark");
        case "simple":
            return("font-serif text-accent-dark");
        case "title":
            return("font-bold text-xl text-primary");
        case "main":
            return("bg-accent-dark text-background px-5 py-2.5 rounded-[999px] hover:bg-accent");
        case "link":
            return ("inline-flex items-center gap-2 bg-primary text-background px-4 py-2 rounded-[999px] hover:bg-primary-dark");
        case "chip":
            return (selected
                        ? "rounded-full border px-4 py-1.5 text-sm font-semibold transition-colors border-primary bg-primary text-white"
                        : "rounded-full border px-4 py-1.5 text-sm font-semibold transition-colors border bg-white text-accent hover:border-primary"
                    );
    }
}

export function Button({
    variant,
    children,
    className,
    selected,
    ...props
}: ButtonProps) {
    const style = getButtonStyle(variant, selected);

    return (
        <button
            {...props}
            className={`${style} ${className ?? ""}`}
        >
            {children}
        </button>
    );
}
