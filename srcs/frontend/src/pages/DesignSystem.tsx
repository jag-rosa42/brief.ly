import { Button, buttonVariants } from "@/shared/components/Button";
import { Link } from "@/shared/components/Link";
import { Text, textVariants } from "@/shared/components/Text";
import { Division, divVariants } from "@/shared/components/Division";
import { Dropdown } from "@/shared/components/Dropdown";
import { useState, type ChangeEvent } from "react";
import {Tabs, type TabItem} from "@/shared/components/Tabs";
import { Input } from "@/shared/components/Input";
import { Form } from "@/shared/components/Form";


const tabs: TabItem[] = [
	{
        value: "tab-a",
		label: "Tab A",
		content: (
			<ItemList
			items={[
				{ title: "Title 1", text: "Some text for Item 1."},
				{ title: "Title 2", text: "Some text for item 2"},
			]}
			/>
		),
	},
	{
        value: "tab-b",
		label: "Tab B",
		content: (
			<ItemList
			items={[
				{ title: "Title 3", text: "Some text for Item 3."},
				{ title: "Title 4", text: "Some text for Item 4"},
			]}
			/>
		),
	},
];

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

export function DesignSystem() {
        const [profile, setProfile] = useState({
        interest1: "",
        interest2: "",
        interest3: "",
    });
    const [lastName, setLastName] = useState("");
    const [firstName, setFirstName] = useState("");
    const [password, setPassword] = useState("");

    const handleChange = (e: ChangeEvent<HTMLSelectElement>) => {
        const {name,value} = e.target;
        setProfile((prev) => ({ ...prev, [name]: value}));
    };
    return (
        <div className="bg-gray-300 min-h-screen flex flex-col gap-4 p-4">
            <div className="flex gap-2">
                {buttonVariants.map((variant) => (
                    <Button key={variant} variant={variant}>
                        {variant} button
                    </Button>
                ))}
            </div>
            <div className="flex gap-2">
                {buttonVariants.map((variant) => (
                    <Link key={variant} to="/designsystem" variant={variant}>
                        {variant} link
                    </Link>
                ))}
            </div>
            <div className="flex flex-col gap-2">
                {textVariants.map((variant) => (
                    <Text key={variant} variant={variant}>
                        {variant} text
                    </Text>
                ))}
            </div>
            <div className="flex gap-4">
                {divVariants.map((variant) => (
                    <Division key={variant} variant={variant}>
                        {variant} division with some sample content inside to check the layout.
                    </Division>
                ))}
            </div>
            <div>
                <Dropdown
                    variant="main"
                    label="Interest1"
                    name="interest1"
                    value={profile.interest1}
                    onChange={handleChange}
                    options={[
                        {value: "AI", label: "AI"},
                        {value: "Finance", label: "Finance"},
                        {value: "Nature", label: "Nature"},
                    ]}
                />
                </div>
            <div>
                <Dropdown
                    variant="main"
                    label="Interest2"
                    name="interest2"
                    value={profile.interest2}
                    onChange={handleChange}
                    options={[
                        {value: "AI", label: "AI"},
                        {value: "Finance", label: "Finance"},
                        {value: "Nature", label: "Nature"},
                    ]}
                />
                </div>
            <div>
                <Dropdown
                    variant="main"
                    label="Interest3"
                    name="interest3"
                    value={profile.interest3}
                    onChange={handleChange}
                    options={[
                        {value: "AI", label: "AI"},
                        {value: "Finance", label: "Finance"},
                        {value: "Nature", label: "Nature"},
                    ]}
                />
                </div>
                <div className="flex flex-col gap-4">
		            <Tabs tabs={tabs} variant="main" />
		            <Tabs tabs={tabs} variant="sub" />
		        </div>
                <div className="flex flex-col gap-4">
                    <Input
                        variant="sub"
                        label="First name"
                        name="firstName"
                        value={firstName}
                        onChange={(e) => setFirstName(e.target.value)}
                    />
                    <Input
                        variant="sub"
                        label="Last name"
                        name="lastName"
                        value={lastName}
                        onChange={(e) => setLastName(e.target.value)}
                    />
                    <Input
                        variant="sub"
                        label="Password"
                        name="password"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                    />
                </div>
                <Form
                    title="Test Form"
                    
                    actions={
                        <>
                            <Button variant="primary" type="submit">Save</Button>
                            <Button variant="secondary" type="button">Back</Button>
                        </>
                    }
                    >
                    <Input
                        variant="sub"
                        label="First name"
                        name="firstName"
                        value={firstName}
                        onChange={(e) => setFirstName(e.target.value)}
                    />
                    <Input
                        variant="sub"
                        label="Last name"
                        name="lastName"
                        value={lastName}
                        onChange={(e) => setLastName(e.target.value)}
                    />
                    <Input
                        variant="sub"
                        label="Password"
                        name="password"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                    />
                    <Dropdown
                        variant="main"
                        label="Interest3"
                        name="interest3"
                        value={profile.interest3}
                        onChange={handleChange}
                        options={[
                            {value: "AI", label: "AI"},
                            {value: "Finance", label: "Finance"},
                            {value: "Nature", label: "Nature"},
                    ]}
                />
                    </Form>
                </div>
    );
}







