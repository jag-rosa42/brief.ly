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
				target: "http://identity:8000",
				secure: false,
				changeOrigin: true,
				rewrite: (p) => p.replace(/^\/api\/identity/,""),
			},
		},
		...(hmrHost
			? {
				hmr: {
					host: hmrHost,
					protocol: "ws",
					clientPort:
						Number(process.env.VITE_HMR_CLIENT_PORT ?? 5173),
				},
			}
			: {}),
		watch: {
			usePolling,
		},
	},
});
