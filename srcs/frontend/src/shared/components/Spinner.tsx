export function Spinner() {
	return (
		<div role="status" aria-label="Loading" className="flex justify-center p-8">
			<div className="h-10 w-10 animate-spin rounded-full border-4 border-secondary border-t-primary" />
		</div>
	);
}
