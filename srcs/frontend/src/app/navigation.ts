export const DASHBOARD_TABS: readonly string[] = [
	"brief",
	"profile",
	"saved",
	"publicapikey",
] as const;
export type DashboardTab = (typeof DASHBOARD_TABS)[number];

// sessionStorage key of the last page visited while logged in.
export const LAST_PATH = "lastPath";

// Pages only for logged-out users: never saved as the last path.
export const GUEST_PATHS = ["/signup", "/login"];
