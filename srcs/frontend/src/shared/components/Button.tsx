import type { ReactNode } from "react";
import { Link } from "react-router-dom";

interface ButtonProps {
    style: string;
    type: "link" | "submit" | "button";
    onClick?: () => void
    link?: string;
    disabled?: boolean;
    children: ReactNode;
}

export function getButtonStyle(style: string): string
{
    switch(style) {
        case "Header1":
            return ("text-primary px-4 py-2 border-1 rounded border-primary \
                hover:border-primary-dark hover:text-primary-dark");
        case "Header2":
            return("bg-primary text-background px-4 py-2 rounded \
                hover:bg-primary-dark");
        case "Footer":
            return("text-background");
        case "Title":
            return("font-bold text-xl text-primary");
        default:
                return("") ;
    }
}

export function Button(prop: ButtonProps) {
    var style: string;

    style = getButtonStyle(prop.style);
    switch (prop.type) {
	case "link":
        return(
            <Link to={prop.link ?? "/"} className={style}>{prop.children}</Link>
        );
	case "submit":
        return(
            <button type="submit" className={style} disabled={prop.disabled}>{prop.children}</button>
        );
	case "button":
        return(
            <button type="button" className={style} onClick={prop.onClick}>{prop.children}</button>
        );
    }
}
