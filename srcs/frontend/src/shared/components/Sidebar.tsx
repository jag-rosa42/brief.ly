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
		<aside className="flex flex-col gap-8 h-screen sticky top-0 overflow-y-auto shrink-0 w-56 px-6 py-4 bg-background shadow-relief-up ">
			<Logo />
			<Tabs
				tabs={tabs}
				variant="side"
				appearance="neomorphic"
				activeValue={activeTab}
				onTabChange={onSelectTab}
			/>

			<Button type="button" variant="main" className="mt-auto" onClick={onDisconnect}>
				Log out
			</Button>
		</aside>
	);
}
