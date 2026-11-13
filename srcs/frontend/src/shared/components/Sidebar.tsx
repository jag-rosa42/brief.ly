import { Button } from "@/shared/components/Button";
import { Logo } from "@/shared/components/Logo";
import { Tabs } from "@/shared/components/Tab";
import type { TabItem } from "@/shared/components/Tab";

interface SidebarProps {
	tabs: TabItem[];
	activeTab: string;
	onSelectTab: (value: string) => void;
	onDisconnect: () => void;
}

export function Sidebar({ tabs, activeTab, onSelectTab, onDisconnect }: SidebarProps) {
	return (
		// Mobile: a top bar, logo and "Log out" on the first row, the tabs on the
		// second (a grid). From md: a sticky column on the left (flex), with
		// "Log out" moved to the bottom by md:order-last.
		<aside className="grid grid-cols-[1fr_auto] items-center gap-3 px-4 py-3 border-b border-secondary md:flex md:flex-col md:items-stretch md:gap-8 md:h-screen md:sticky md:top-0 md:overflow-y-auto md:shrink-0 md:w-56 md:px-6 md:py-4 md:border-b-0 md:border-r">
			<Logo />
			<Button
				type="button"
				variant="main"
				className="md:order-last md:mt-auto"
				onClick={onDisconnect}
			>
				Log out
			</Button>
			{/* min-w-0: lets the tab row scroll sideways instead of widening the grid. */}
			<Tabs
				tabs={tabs}
				variant="side"
				className="col-span-2 min-w-0"
				activeValue={activeTab}
				onTabChange={onSelectTab}
			/>
		</aside>
	);
}
