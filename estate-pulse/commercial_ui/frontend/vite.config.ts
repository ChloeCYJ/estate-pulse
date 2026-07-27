import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig(({ command }) => ({
  plugins: [react()],
  define:
    command === "build"
      ? {
          "process.env.NODE_ENV": "\"production\""
        }
      : undefined,
  build: {
    outDir: "./build",
    emptyOutDir: false,
    sourcemap: false,
    lib: {
      entry: "./src/index.tsx",
      formats: ["es"],
      fileName: () => "commercial-ui.js"
    },
    rollupOptions: {
      output: {
        assetFileNames: (assetInfo) => {
          if (assetInfo.name?.endsWith(".css")) {
            return "commercial-ui.css";
          }
          return "[name][extname]";
        }
      }
    }
  },
  test: {
    environment: "jsdom",
    setupFiles: "./src/test-setup.ts"
  }
}));
