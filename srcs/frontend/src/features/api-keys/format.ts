export function formatDate(iso: string): string {
	return new Date(iso).toLocaleString("en-GB", {
		day: "2-digit",
		month: "2-digit",
		year: "numeric",
		hour: "2-digit",
		minute: "2-digit",
	});
}

export function isExpired(iso: string): boolean {
	return Date.parse(iso) < Date.now();
}
