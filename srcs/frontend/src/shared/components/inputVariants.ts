export const inputVariants = ["main", "sub"] as const;
export type InputVariant = typeof inputVariants[number];

export function getInputStyle(variant:InputVariant): string
{
	switch(variant) {
		case "main":
			return("border rounded-[18px] px-4 py-3");
		case "sub":
			return("border rounded-[18px] px-3 py-2");
	}
}