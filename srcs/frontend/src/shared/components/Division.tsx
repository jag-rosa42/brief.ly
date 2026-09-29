export const divVariants = ["featurecard", "content", "page"] as const;
export type DivVariant = typeof divVariants[number];

interface DivProps extends React.HTMLAttributes<HTMLDivElement>
{
    variant: DivVariant;
}

export function getDivStyle(style: DivVariant): string
{
    switch(style) {
        case "featurecard":
            return ("bg-white border border rounded-xl p-6 flex flex-col gap-y-3");
        case "content":
            return ("text-accent leading-relaxed");
        case "page":
            return ("bg-background flex flex-col items-center pt-12 px-4");
    }
}

export function Division({
    variant,
    children,
    className,
    ...props
}: DivProps) {
    const divVariant = getDivStyle(variant);

    return (
        <div
            {...props}
            className={`${divVariant} ${className ?? ""}`}
        >
            {children}
        </div>
    );
}
