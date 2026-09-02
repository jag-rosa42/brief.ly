import { describe, it, expect } from "vitest";
import {
	sumArray,
	doubleAll,
	getAdultNames,
	greet,
	mergeSettings,
} from "./exercise1";

describe("sumArray", () => {
	it("sums numbers", () => {
		expect(sumArray([1, 2, 3])).toBe(6);
		expect(sumArray([])).toBe(0);
	});
});

describe("doubleAll", () => {
	it("doubles every number", () => {
		expect(doubleAll([1, 2, 3])).toEqual([2, 4, 6]);
	});
});

describe("getAdultNames", () => {
	it("keeps only adults' names", () => {
		const people = [
			{ name: "Alice", age: 20 },
			{ name: "Bob", age: 15 },
			{ name: "Chloé", age: 18 },
		];
		expect(getAdultNames(people)).toEqual(["Alice", "Chloé"]);
	});
});

describe("greet", () => {
	it("uses default greeting", () => {
		expect(greet("Alice")).toBe("Hello, Alice!");
	});
	it("uses custom greeting", () => {
		expect(greet("Bob", "Salut")).toBe("Salut, Bob!");
	});
});

describe("mergeSettings", () => {
	it("merges, with overrides winning", () => {
		expect(mergeSettings({ a: 1, b: 2 }, { b: 3, c: 4 })).toEqual({
			a: 1,
			b: 3,
			c: 4,
		});
	});
});
