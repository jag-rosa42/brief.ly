import { useState } from "react";
import type { ReactNode } from "react";
import { Button } from "@/shared/components/Button";

export type TabItem = {
	value: string;
	label: string;
	content: ReactNode;
};

export const tabVariant = ["main", "sub"] as const;
export type TabVariant = typeof tabVariant[number];

export function getTabStyle(style:TabVariant): string {
	switch(style) {
		case "main":
			return ("flex gap-2 border-b border-gray-300");
		case "sub":
			return("flex gap-1 bg-gray-800 p-1 rounded");
	}
}

export function getTabButtonStyle(isActive: boolean): string {
	if (isActive)
		return "px-4 py-2 border-b-2 border-blue-600 font-bold text-blue-600";
	return "px-4 py-2 text-gray-500";
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
	const handleTabChange = (tab: TabItem, index:number) =>
		{
			setActiveIndex(index);
			onTabChange?.(tab.value);
		};
	const listStyle = getTabStyle(variant);
	return(
		<div className={className}>
			<div role="tablist" className={listStyle}>
				{tabs.map((tab,index) => {
					const isActive = activeIndex === index;
					return(
						<Button
							key={tab.label}
							variant="text"
							role="tab"
							onClick={() =>handleTabChange(tab, index)}
							className={getTabButtonStyle(isActive)}
							>
								{tab.label}
							</Button>
					  );
				})}
			</div>
			<div role="tabpanel" className="mt-4">
				{tabs[activeIndex].content}
			</div>
		</div>
	);
}