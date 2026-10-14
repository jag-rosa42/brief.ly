import { Button } from "@/shared/components/Button";
import { Division } from "@/shared/components/Division";
import { Link } from "@/shared/components/Link";

export interface SidebarTab {
	id: string;
	label: string;
	disabled?: boolean;
}

interface SidebarProps {
	tabs: SidebarTab[];
	activeTab: string;
	onSelectTab: (id: string) => void;
	onDisconnect: () => void;
}

export function Sidebar({
	tabs,
	activeTab,
	onSelectTab,
	onDisconnect,
}: SidebarProps) {
	return (
		<aside className="flex flex-col gap-8 h-screen sticky top-0 overflow-y-auto shrink-0 px-6 py-4 border-r border-secondary">
			<Link to="/" variant="title">Brief<span className="text-secondary">.ly</span></Link>

			<Division variant="stack" role="tablist" aria-orientation="vertical">
				{tabs.map((tab) => (
					<Button
						key={tab.id}
						type="button"
						role="tab"
						aria-selected={tab.id === activeTab}
						variant={tab.id === activeTab ? "secondary" : "primary"}
						disabled={tab.disabled}
						onClick={() => onSelectTab(tab.id)}
					>
						{tab.label}
					</Button>
				))}
			</Division>
			
			<Button type="button" variant="main" className="mt-auto" onClick={onDisconnect}>
				Log out
			</Button>
		</aside>
	);
}