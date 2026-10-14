import { useState } from "react";
import type { ReactNode } from "react";
import { Button } from "@/shared/components/Button";

export type TabItem = {
value: string;
label: string;
content: ReactNode;
};

export const tabVariant = ["main", "sub", "pill"] as const;
export type TabVariant = typeof tabVariant[number];

export function getTabStyle(style:TabVariant): string {
	switch(style) {
		case "main":
			return ("flex gap-2 border-b border-gray-300");
		case "sub":
			return("flex gap-1 bg-gray-800 p-1 rounded");
		case "pill":
			return("inline-flex w-fit gap-1 rounded-full bg-white/50 p-1 backdrop-blur-sm");
}
}

export function getTabButtonStyle(isActive: boolean, variant: TabVariant): string {
	if (variant === "pill") {
		if (isActive)
			return("rounded-full bg-white px-4 py-1.5 text-sm font-semibold text-primary-dark shadow-sm");
		return ("rounded-full px-4 py-1.5 text-sm text-info hover:text-accent");
	}
	if (isActive)
		return ("px-4 py-2 border-b-2 border-primary font-bold text-primary");
	return ("px-4 py-2 text-gray-500 hover:text-primary");
}

type TabsProps = {
	tabs: TabItem[];
	variant: TabVariant;
	className?: string;
	onTabChange?: (value: string) => void;
};

export function Tabs({
	tabs,
	variant,
	className = "",
	onTabChange,
}: TabsProps) {
	const [activeIndex, setActiveIndex] = useState(0);
	const currentIndex = Math.min(activeIndex, tabs.length - 1);
	const handleTabChange = (tab: TabItem, index:number) => {
		setActiveIndex(index);
		onTabChange?.(tab.value);
	};
	const listStyle = getTabStyle(variant);
	return(
	<div className={className}>
		<div role="tablist" className={listStyle}>
			{
			tabs.map((tab,index) => {
				const isActive = activeIndex === index;
				return(
				<Button
				key={tab.value}
				variant="simple"
				role="tab"
				onClick={() =>handleTabChange(tab, index)}
				className={getTabButtonStyle(isActive, variant)}
				>
					{tab.label}
					</Button>
					);
					})}
					</div>
				{tabs.length > 0 && (
					<div role="tabpanel" className="mt-4">
						{tabs[currentIndex].content}
						</div>
				)}
						</div>
		);
}