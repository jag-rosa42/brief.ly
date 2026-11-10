export const divVariants = [
	"featurecard",
	"content",
	"page",
	"dashboardcard",
	"stack",
	"dashboardpage",
] as const;
export type DivVariant = (typeof divVariants)[number];

export function getDivStyle(style: DivVariant): string {
	switch (style) {
		case "featurecard":
			return "bg-white border border rounded-xl p-6 flex flex-col gap-y-3";
		case "content":
			return "text-accent leading-relaxed";
		case "page":
			return "bg-background flex flex-col items-center pt-12 px-4";
		case "dashboardcard":
			return "flex flex-col gap-y-3 rounded-[2rem] bg-[#f1e8dc] p-6 shadow-[10px_12px_24px_#c5b6a580,-7px_-7px_18px_#fff9f099]";
		case "stack":
			return "flex flex-col gap-2";
		case "dashboardpage":
			return "mx-auto flex w-full flex-col";
	}
}
