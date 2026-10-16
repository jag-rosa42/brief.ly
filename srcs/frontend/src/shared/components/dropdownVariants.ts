export interface DropdownOption {
	value: string;
	label: string;
};

export const dropdownVariant = ["main", "filter"] as const;
export type DropdownVariant = typeof dropdownVariant[number];

export function getDropdownStyle(variant:DropdownVariant):string
{
	switch(variant) {
		case "main":
			return("border rounded px-3 py-2 bg-white");
		case "filter":
			return("border rounded px-3 py-2 bg-black");
	}
}