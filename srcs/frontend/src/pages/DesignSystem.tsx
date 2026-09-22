import { Button, buttonVariants } from "@/shared/components/Button";
import { Link } from "@/shared/components/Link";
import { Text, textVariants } from "@/shared/components/Text";
import { Division, divVariants } from "@/shared/components/Division";
import { Dropdown } from "@/shared/components/Dropdown";
import { useState, type ChangeEvent } from "react";


export function DesignSystem() {
        const [profile, setProfile] = useState({
        interest1: "",
        interest2: "",
        interest3: "",
    });

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
            <div className="flex flex-col gap-1">
                Interest1:
                <Dropdown
                    variant="main"
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
                <div className="flex flex-col gap-1">
                Interest2:
                <Dropdown
                    variant="main"
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
                <div className="flex flex-col gap-1">
                Interest3:
                <Dropdown
                    variant="main"
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
            </div>
    );
}
