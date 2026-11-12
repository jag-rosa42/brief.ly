import { useState } from "react";
import type { ReactNode } from "react";
import { Button } from "@/shared/components/Button";
import type { Appearance } from "@/shared/components/neomorphicVariants";
import {
	getTabStyle,
	getTabButtonStyle,
	getTabButtonVariant,
} from "@/shared/components/tabVariants";
import type { TabVariant } from "@/shared/components/tabVariants";

export type { TabVariant };

export interface TabItem {
	value: string;
	label: string;
	content?: ReactNode;
	disabled?: boolean;
}

type TabsProps = {
	tabs: TabItem[];
	className?: string;
	activeValue?: string;
	onTabChange?: (value: string) => void;
} & (
	| { variant: "pill" | "side"; appearance?: Appearance }
	| { variant: Exclude<TabVariant, "pill" | "side">; appearance?: "classic" }
);

export function Tabs({
	tabs,
	variant,
	appearance = "classic",
	className = "",
	activeValue,
	onTabChange,
}: TabsProps) {
	const [internalIndex, setInternalIndex] = useState(0);
	let currentIndex = Math.min(internalIndex, tabs.length - 1); // par défaut : l'état interne
	if (activeValue !== undefined) {
		const controlledIndex = tabs.findIndex((t) => t.value === activeValue);
		if (controlledIndex >= 0) {
			currentIndex = controlledIndex; // le parent a la priorité
		}
	}
	const handleTabChange = (tab: TabItem, index: number) => {
		setInternalIndex(index);
		onTabChange?.(tab.value);
	};
	const currentContent = tabs[currentIndex]?.content;
	return (
		<div className={className}>
			<div role="tablist" className={`${getTabStyle(variant, appearance)} w-full`}>
				{tabs.map((tab, index) => {
					const isActive = currentIndex === index;
					return (
						<Button
							key={tab.value}
							type="button"
							variant={getTabButtonVariant(variant)}
							relief={
								variant === "side" && appearance === "neomorphic"
									? isActive
										? "down"
										: "none"
									: "none"
							}
							role="tab"
							aria-selected={isActive}
							disabled={tab.disabled}
							onClick={() => handleTabChange(tab, index)}
							className={`${getTabButtonStyle(isActive, variant, appearance)} min-w-0 flex-1 truncate`}
						>
							{tab.label}
						</Button>
					);
				})}
			</div>
			{currentContent && (
				<div role="tabpanel" className="mt-4">
					{currentContent}
				</div>
			)}
		</div>
	);
}
