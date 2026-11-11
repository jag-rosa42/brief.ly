import { useState, type ReactNode } from "react";
import { useNotify } from "@/app/useNotify";
import { ArticleCard } from "@/shared/components/ArticleCard";
import type { Article } from "@/shared/components/ArticleModal";
import { Button } from "@/shared/components/Button";
import { buttonVariants } from "@/shared/components/buttonVariants";
import { Card } from "@/shared/components/Card";
import { Division } from "@/shared/components/Division";
import { Dropdown } from "@/shared/components/Dropdown";
import { FilterChip } from "@/shared/components/FilterChip";
import { Icon } from "@/shared/components/Icon";
import { ICON_NAMES } from "@/shared/components/iconPaths";
import { Input } from "@/shared/components/Input";
import { Link } from "@/shared/components/Link";
import { Logo } from "@/shared/components/Logo";
import { notificationVariants } from "@/shared/components/notificationVariants";
import { Spinner } from "@/shared/components/Spinner";
import { Tabs } from "@/shared/components/Tab";
import { tabVariant } from "@/shared/components/tabVariants";
import { Text } from "@/shared/components/Text";
import { textVariants } from "@/shared/components/textVariants";

// The design system of Brief.ly on one page: its colors, fonts and icons,
// and every shared component with its variants. Public, to show it without
// an account.

// The tokens of index.css (@theme). Written out in full: Tailwind only
// generates the classes it finds as is in the code.
const COLORS = [
	{ name: "primary", swatch: "bg-primary", value: "#d4751a" },
	{ name: "secondary", swatch: "bg-secondary", value: "#b79a7a" },
	{ name: "accent", swatch: "bg-accent", value: "#493a33" },
	{ name: "background", swatch: "bg-background", value: "#f2ebe0" },
	{ name: "error", swatch: "bg-error", value: "#e62e1c" },
	{ name: "info", swatch: "bg-info", value: "#7a807a" },
	{ name: "success", swatch: "bg-success", value: "#778b6b" },
];

const SHADES = [
	{ name: "primary", light: "bg-primary-light", base: "bg-primary", dark: "bg-primary-dark" },
	{
		name: "secondary",
		light: "bg-secondary-light",
		base: "bg-secondary",
		dark: "bg-secondary-dark",
	},
	{ name: "accent", light: "bg-accent-light", base: "bg-accent", dark: "bg-accent-dark" },
	{
		name: "background",
		light: "bg-background-light",
		base: "bg-background",
		dark: "bg-background-dark",
	},
];

const SAMPLE_ARTICLE: Article = {
	id: "design-page-sample",
	title: "Open-source models narrow the enterprise gap",
	category: "Technologies",
	source: "TechDaily",
	url: null,
	summary: "Smaller teams gain access to capable models, at a fraction of the cost.",
	readingTime: 3,
};

const TOPICS = [
	{ value: "technologies", label: "Technologies" },
	{ value: "health", label: "Health" },
	{ value: "science", label: "Science" },
];

function Section({ title, children }: { title: string; children: ReactNode }) {
	return (
		<section className="flex flex-col gap-4">
			<Text variant="subheading">{title}</Text>
			{children}
		</section>
	);
}

// A row of examples, each with the name of what it shows.
function Example({ name, children }: { name: string; children: ReactNode }) {
	return (
		<div className="flex flex-col items-start gap-2">
			<Text variant="label" className="text-info">
				{name}
			</Text>
			{children}
		</div>
	);
}

export function DesignPage() {
	const { notify } = useNotify();
	const [chips, setChips] = useState<string[]>(["technologies"]);
	const [text, setText] = useState("");
	const [choice, setChoice] = useState("");
	const [saved, setSaved] = useState(false);

	function toggleChip(value: string) {
		setChips((prev) => (prev.includes(value) ? prev.filter((v) => v !== value) : [...prev, value]));
	}

	return (
		<main className="mx-auto flex max-w-5xl flex-col gap-14 px-6 py-16">
			<div className="flex flex-col gap-3">
				<Text variant="title">Design system</Text>
				<Text variant="lead">The colors, fonts, icons and components Brief.ly is built with.</Text>
			</div>

			<Section title="Colors">
				<div className="grid grid-cols-2 gap-4 sm:grid-cols-4 lg:grid-cols-7">
					{COLORS.map((color) => (
						<div key={color.name} className="flex flex-col gap-2">
							<div className={`h-16 rounded-xl border border-accent/10 ${color.swatch}`} />
							<Text variant="body" className="text-sm font-semibold">
								{color.name}
							</Text>
							<Text variant="body" className="text-xs text-info">
								{color.value}
							</Text>
						</div>
					))}
				</div>
				<Example name="Shades: light, base, dark">
					<div className="flex flex-wrap gap-6">
						{SHADES.map((shade) => (
							<div key={shade.name} className="flex flex-col gap-2">
								<div className="flex overflow-hidden rounded-xl border border-accent/10">
									<div className={`h-10 w-12 ${shade.light}`} />
									<div className={`h-10 w-12 ${shade.base}`} />
									<div className={`h-10 w-12 ${shade.dark}`} />
								</div>
								<Text variant="body" className="text-xs">
									{shade.name}
								</Text>
							</div>
						))}
					</div>
				</Example>
			</Section>

			<Section title="Typography">
				<div className="grid gap-4 sm:grid-cols-2">
					<Example name="Sofia Sans (font-sans): text and interface">
						<p className="font-sans text-3xl text-accent-dark">Aa Bb Cc 0123</p>
					</Example>
					<Example name="Fraunces (font-serif): titles and lead">
						<p className="font-serif text-3xl text-accent-dark">Aa Bb Cc 0123</p>
					</Example>
				</div>
				<div className="flex flex-col gap-4">
					{textVariants.map((variant) => (
						<Example key={variant} name={`Text ${variant}`}>
							<Text variant={variant}>Your morning, in a few minutes</Text>
						</Example>
					))}
				</div>
			</Section>

			<Section title="Icons">
				<div className="flex flex-wrap gap-8 text-accent-dark">
					{ICON_NAMES.map((name) => (
						<Example key={name} name={name}>
							<div className="flex items-end gap-3">
								<Icon name={name} size="sm" />
								<Icon name={name} size="md" />
								<Icon name={name} size="lg" className="text-primary" />
							</div>
						</Example>
					))}
				</div>
			</Section>

			<Section title="Buttons and links">
				<div className="flex flex-wrap items-end gap-6">
					{buttonVariants.map((variant) => (
						<Example key={variant} name={`Button ${variant}`}>
							<Button type="button" variant={variant}>
								Button
							</Button>
						</Example>
					))}
					<Example name="Button chip, selected">
						<Button type="button" variant="chip" selected>
							Selected
						</Button>
					</Example>
					<Example name="Disabled">
						<Button type="button" variant="secondary" disabled className="opacity-50">
							Disabled
						</Button>
					</Example>
					<Example name="With an icon">
						<Button type="button" variant="link">
							<Icon name="bookmark" size="sm" />
							Save
						</Button>
					</Example>
				</div>
				<div className="flex flex-wrap items-end gap-6">
					<Example name="Link main">
						<Link to="/designpage" variant="main">
							Get started
						</Link>
					</Example>
					<Example name="Link simple">
						<Link to="/designpage" variant="simple">
							Terms of Service
						</Link>
					</Example>
					<Example name="Logo">
						<Logo />
					</Example>
				</div>
			</Section>

			<Section title="Forms">
				<div className="grid gap-6 sm:grid-cols-2">
					<Input
						variant="main"
						label="Input main"
						name="design-main"
						placeholder="you@example.com"
						value={text}
						onChange={(e) => setText(e.target.value)}
					/>
					<Input
						variant="sub"
						label="Input sub, with a hint"
						name="design-sub"
						placeholder="Search"
						info="A hint under the field."
						value={text}
						onChange={(e) => setText(e.target.value)}
					/>
					<Input
						variant="main"
						label="Input with an error"
						name="design-error"
						error="This field is required."
						value=""
						onChange={() => undefined}
					/>
					<Dropdown
						variant="main"
						label="Dropdown main"
						name="design-dropdown"
						options={TOPICS}
						value={choice}
						onChange={(e) => setChoice(e.target.value)}
					/>
				</div>
				<Example name="Filter chips">
					<div className="flex flex-wrap gap-2">
						{TOPICS.map((topic) => (
							<FilterChip
								key={topic.value}
								options={topic}
								selected={chips.includes(topic.value)}
								onToggle={toggleChip}
							/>
						))}
						<FilterChip
							options={{ value: "disabled", label: "Disabled" }}
							selected={false}
							disabled
							onToggle={() => undefined}
						/>
					</div>
				</Example>
			</Section>

			<Section title="Tabs">
				<div className="grid gap-8 sm:grid-cols-2">
					{tabVariant.map((variant) => (
						<Example key={variant} name={`Tabs ${variant}`}>
							<Tabs
								variant={variant}
								tabs={TOPICS.map((topic) => ({ value: topic.value, label: topic.label }))}
							/>
						</Example>
					))}
				</div>
			</Section>

			<Section title="Cards">
				<div className="grid gap-6 md:grid-cols-3">
					<Card title="Card" description="A title, a description and its content." />
					<Division variant="featurecard">
						<Text variant="heading">Division featurecard</Text>
						<Text variant="body">The cards of the landing page.</Text>
					</Division>
					<Division variant="dashboardcard">
						<Text variant="heading">Division dashboardcard</Text>
						<Text variant="body">The surfaces of the dashboard.</Text>
					</Division>
				</div>
				<Example name="Article card">
					<ArticleCard
						className="max-w-md"
						article={SAMPLE_ARTICLE}
						isSaved={saved}
						onToggleSave={() => setSaved((prev) => !prev)}
						onReadMore={() => notify("Read More opens the article.", "info")}
					/>
				</Example>
			</Section>

			<Section title="Feedback">
				<div className="flex flex-wrap items-end gap-6">
					{notificationVariants.map((variant) => (
						<Example key={variant} name={`Notification ${variant}`}>
							<Button
								type="button"
								variant="primary"
								onClick={() => notify(`Example notification (${variant}).`, variant)}
							>
								Show
							</Button>
						</Example>
					))}
					<Example name="Spinner">
						<Spinner />
					</Example>
				</div>
			</Section>
		</main>
	);
}
