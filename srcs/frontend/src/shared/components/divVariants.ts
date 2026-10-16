export const divVariants = ["featurecard", "content", "page", "dashboardcard", "stack", "dashboardpage"] as const;
export type DivVariant = typeof divVariants[number];

export function getDivStyle(style: DivVariant): string
{
	switch(style) {
		case "featurecard":
			return ("bg-white border border rounded-xl p-6 flex flex-col gap-y-3");
		case "content":
			return ("text-accent leading-relaxed");
		case "page":
			return ("bg-background flex flex-col items-center pt-12 px-4");
		case "dashboardcard":
			return("bg-white/60 border border-white/70 rounded-3xl p-6 flex flex-col gap-y-3 shadow-soft backdrop-blur-sm");
		case "stack":
			return ("flex flex-col gap-2");
		case "dashboardpage":
			return ("flex flex-col mx-auto w-full p-6");
	}
}