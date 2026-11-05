/// <reference types="vitest" />

import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "node:path";
import tailwindcss from "@tailwindcss/vite";

// Enables polling (repeated file-change checks) when VITE_USE_POLLING is "true".
// It make sure that the live-reload works both on host and inside a container.
const usePolling = process.env.VITE_USE_POLLING === "true";
// Optional host the browser uses to connect to Vite's live-reload (HMR) server.
const hmrHost = process.env.VITE_HMR_HOST;
// Protocol of that connection. In Docker, the page comes from the gateway over
// HTTPS, so the browser must use "wss" (compose.override.yaml sets it, with the
// gateway's port as VITE_HMR_CLIENT_PORT); the gateway forwards it to Vite.
const hmrProtocol = process.env.VITE_HMR_PROTOCOL === "wss" ? "wss" : "ws";
// Target of the /api/identity proxy, used only by `make frontend` on the host:
// the locally exposed identity service (make run SERVICE=identity).
// In Docker, the gateway routes /api before a request reaches Vite.
const identityTarget = process.env.IDENTITY_URL ?? "http://localhost:8081";
// Target of the /api/personalization proxy, used only by `make frontend` on the
// host: the locally exposed personalization service (make run SERVICE=personalization).
// In Docker, the gateway routes /api before a request reaches Vite.
const personalizationTarget = process.env.PERSONALIZATION_URL ?? "http://localhost:8082";

export default defineConfig({
	base: "/",
	plugins: [react(), tailwindcss()],
	resolve: {
		alias: {
			"@": path.resolve(__dirname, "./src"),
		},
	},
	server: {
		host: true,
		port: 5173,
		strictPort: true,
		proxy: {
			"/api/identity": {
				target: identityTarget,
				secure: false,
				changeOrigin: true,
				rewrite: (p) => p.replace(/^\/api\/identity/, ""),
			},
			"/api/personalization": {
				target: personalizationTarget,
				secure: false,
				changeOrigin: true,
				rewrite: (p) => p.replace(/^\/api\/personalization/, ""),
			},
		},
		...(hmrHost
			? {
					hmr: {
						host: hmrHost,
						protocol: hmrProtocol,
						clientPort: Number(process.env.VITE_HMR_CLIENT_PORT ?? 5173),
					},
				}
			: {}),
		watch: {
			usePolling,
		},
	},
});
