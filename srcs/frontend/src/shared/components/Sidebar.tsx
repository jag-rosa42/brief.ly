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
		<aside className="relative z-10 flex w-full shrink-0 flex-col gap-4 bg-[#f1e8dc] p-4 shadow-[0_8px_18px_#c5b6a52e] md:sticky md:top-0 md:h-screen md:w-[clamp(220px,16vw,288px)] md:gap-8 md:overflow-y-auto md:px-6 md:py-9 md:shadow-[12px_0_32px_#c5b6a520]">
			<div className="flex items-center gap-3 font-serif before:grid before:size-12 before:shrink-0 before:place-items-center before:rounded-2xl before:bg-primary before:text-[1.6rem] before:text-[#fff9f0] before:shadow-[5px_8px_16px_#bba68d70] before:content-['B'] [&_a]:whitespace-nowrap [&_a]:text-[1.65rem] [&_a]:text-accent [&_span]:text-accent">
				<Logo />
			</div>
			<Tabs tabs={tabs} variant="side" activeValue={activeTab} onTabChange={onSelectTab} />

			<Button
				type="button"
				variant="main"
				className="mt-auto self-end bg-[#f1e8dc]! px-4 text-accent! shadow-[5px_6px_12px_#c5b6a570,-5px_-5px_12px_#fff9f0] hover:bg-[#f7f0e7]! md:w-full"
				onClick={onDisconnect}
			>
				Log out
			</Button>
		</aside>
	);
}
