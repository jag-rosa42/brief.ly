import { useState } from "react";
import type { ReactNode } from "react";
import { Button } from "@/shared/components/Button";
import {
	getTabStyle,
	getTabButtonVariant,
	getTabButtonStyle,
} from "@/shared/components/tabVariants";
import type { TabVariant } from "@/shared/components/tabVariants";

export type { TabVariant };

export interface TabItem {
	value: string;
	label: string;
	content?: ReactNode;
	disabled?: boolean;
}

interface TabsProps {
	tabs: TabItem[];
	variant: TabVariant;
	className?: string;
	activeValue?: string;
	onTabChange?: (value: string) => void;
}

export function Tabs({ tabs, variant, className = "", activeValue, onTabChange }: TabsProps) {
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
			<div role="tablist" className={getTabStyle(variant)}>
				{tabs.map((tab, index) => {
					const isActive = currentIndex === index;
					return (
						<Button
							key={tab.value}
							type="button"
							variant={getTabButtonVariant(isActive, variant)}
							role="tab"
							disabled={tab.disabled}
							onClick={() => handleTabChange(tab, index)}
							className={getTabButtonStyle(isActive, variant)}
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
