import { describe, it, expect } from "vitest";
import {
	formatPrice,
	nextStatus,
	formatId,
	products,
	getExpensiveProducts,
	type Product,
} from "./exercise2";

describe("formatPrice", () => {
	it("formats a product's price", () => {
		const p: Product = { id: 1, name: "Coffee", price: 12.5 };
		expect(formatPrice(p)).toBe("Coffee - $12.5");
	});
});

describe("nextStatus", () => {
	it("cycles through statuses", () => {
		expect(nextStatus("pending")).toBe("active");
		expect(nextStatus("active")).toBe("done");
		expect(nextStatus("done")).toBe("pending");
	});
});

describe("formatId", () => {
	it("works with a number", () => {
		expect(formatId(5)).toBe("ID-5");
	});
	it("works with a string", () => {
		expect(formatId("abc")).toBe("ID-abc");
	});
});

describe("products (exercise array)", () => {
	it("has at least 3 valid products", () => {
		expect(products.length).toBeGreaterThanOrEqual(3);
		for (const p of products) {
			expect(typeof p.id).toBe("number");
			expect(typeof p.name).toBe("string");
			expect(typeof p.price).toBe("number");
		}
	});
});

describe("getExpensiveProducts", () => {
	const catalog: Product[] = [
		{ id: 1, name: "Cheap", price: 5 },
		{ id: 2, name: "Mid", price: 10 },
		{ id: 3, name: "Pricey", price: 20, description: "fancy" },
	];

	it("keeps only products at or above minPrice", () => {
		expect(getExpensiveProducts(catalog, 10)).toEqual([
			{ id: 2, name: "Mid", price: 10 },
			{ id: 3, name: "Pricey", price: 20, description: "fancy" },
		]);
	});

	it("returns an empty array when nothing matches", () => {
		expect(getExpensiveProducts(catalog, 100)).toEqual([]);
	});
});
