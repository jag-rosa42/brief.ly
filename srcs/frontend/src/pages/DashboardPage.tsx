import { useState } from "react";

interface ListItem {
	title: string;
	text: string;
}

function ItemList({ items }: { items: ListItem[] }) {
	return (
		<ul className="flex flex-col gap-4">
			{items.map((item) => (
				<li key={item.title}>
					<h3 className="font-semibold text-secondary">{item.title}</h3>
					<p className="text-accent">{item.text}</p>
				</li>
			))}
		</ul>
	);
}

const tabs = [
	{
		label: "Tab A",
		content: (
			<ItemList
				items={[
					{ title: "Title 1", text: "Some text for item 1." },
					{ title: "Title 2", text: "Some text for item 2." },
				]}
			/>
		),
	},
	{
		label: "Tab B",
		content: (
			<ItemList
				items={[
					{ title: "Title 3", text: "Some text for item 3." },
					{ title: "Title 4", text: "Some text for item 2." },
				]}
			/>
		),
	},
	{
		label: "Tab C",
		content: (
			<ItemList
				items={[
					{ title: "Title 5", text: "Some text for item 5." },
					{ title: "Title 6", text: "Some text for item 6." },
				]}
			/>
		),
	},
	{
		label: "Tab D",
		content: (
			<ItemList
				items={[
					{ title: "Title 7", text: "Some text for item 7." },
					{ title: "Title 8", text: "Some text for item 8." },
				]}
			/>
		),
	},
];

export function DashboardPage() {
	const [active, setActive] = useState(0);

	return (
		<main className="max-w-4xl mx-auto px-6 py-16">
			<h1 className="text-3xl font-bold text-primary mb-6">Dashboard</h1>
			<nav className="flex gap-4 border-b mb-6">
				{tabs.map((tab, i) => (
					<button
						key={tab.label}
						onClick={() => setActive(i)}
						className={
							i === active
								? "font-bold border-b-2 border-primary pb-2"
								: "text-accent pb-2"
						}
					>
						{tab.label}
					</button>
				))}
			</nav>
			<div>{tabs[active].content}</div>
		</main>
	);
}
