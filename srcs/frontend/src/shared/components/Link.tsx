import { getButtonStyle } from "@/shared/components/Button"
import type { ButtonVariant } from "@/shared/components/Button"
import { useNavigate } from "react-router-dom";


interface LinkProps extends React.AnchorHTMLAttributes<HTMLAnchorElement> {
    variant: ButtonVariant;
    to: string;
    external?: boolean;
}


export function Link({
    variant,
    children,
    to,
    external=false,
    className,
    ...props
}: LinkProps) {
    const navigate = useNavigate();
    const style = getButtonStyle(variant);
    
    function handleClick(e: React.MouseEvent<HTMLAnchorElement>){
        e.preventDefault()
        navigate(to);
    }

    return (
        <a href={to}
            {...props}
            className={`${style} ${className ?? ""}`}
            onClick={handleClick}
             target={external ? "_blank" : props.target}
            rel={external ? "noopener noreferrer" : props.rel}
        >
            {children}
        </a>
    );
}
