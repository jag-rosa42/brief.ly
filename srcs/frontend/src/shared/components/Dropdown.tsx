import type { ChangeEvent } from "react";

export type DropdownOption = {
    value: string;
    label: string;
};

export const dropdownVariant = ["main", "filter"] as const;
export type DropdownVariant = typeof dropdownVariant[number];

export function getDropdownStyle(style:DropdownVariant):string
{
    switch(style) {
        case "main":
            return("border rounded px-3 py-2 bg-white");
        case "filter":
            return("border rounded px-3 py-2 bg-black");
    }
}

type DropdownProps = {
    name: string;
    value: string;
    onChange: (e: ChangeEvent<HTMLSelectElement>) => void;
    options: DropdownOption[];
    placeholder?: string;
    className?: string;
    variant: DropdownVariant;
};

export function Dropdown({
    variant,
    name,
    value,
    onChange,
    options,
    placeholder = "Select...",
    className = "",
}:DropdownProps) {
    const style = getDropdownStyle(variant);
    return (
        <select
            name={name}
            value={value}
            onChange={onChange}
            className={`${style} ${className}`}
            >
                <option value="" disabled>
                    {placeholder}
                </option>
                {options.map((opt) => (
                    <option key={opt.value} value={opt.value}>
                        {opt.label}
                    </option>
                ))}
            </select>
    );
}