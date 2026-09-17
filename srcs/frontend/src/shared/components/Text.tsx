export const textVariants = ["title", "heading", "subheading", "body", "lead"] as const;
export type TextVariant = typeof textVariants[number];

interface TextProps extends React.HTMLAttributes<HTMLParagraphElement>
{
    variant: TextVariant;
}


export function getTextStyle(style: string): string
{
    switch(style) {
        case "title":
            return ("font-serif text-4xl font-bold text-primary");
        case "heading":
            return("font-sans font-semibold text-xl text-accent-dark");
        case "subheading":
            return("font-sans font-semibold text-2xl text-secondary");
        case "body":
            return("text-accent leading-relaxed");
        case "lead":
            return("font-serif text-lg md:text-xl text-accent-dark");
        default:
        return("") ;
    }
}

export function Text({
    variant,
    children,
    className,
    ...props
}: TextProps) {
    const style = getTextStyle(variant);

    return (
        <p
            {...props}
            className={`${style} ${className ?? ""}`}
        >
            {children}
        </p>
    );
}
