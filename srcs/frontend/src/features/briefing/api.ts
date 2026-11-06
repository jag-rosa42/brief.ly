import { apiFetch } from "@/shared/components/api/client";
import type { Briefing } from "@/features/briefing/types";

export function getBriefing(): Promise<Briefing> {
	return apiFetch<Briefing>(`/api/morning-briefing/briefing`);
}
