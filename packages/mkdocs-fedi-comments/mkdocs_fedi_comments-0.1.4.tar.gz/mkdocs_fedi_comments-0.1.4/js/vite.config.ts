import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { resolve } from "path";

export default defineConfig({
  plugins: [react()],
  build: {
    lib: {
      entry: resolve(__dirname, "src/index.tsx"),
      name: "main",
    },
  },
  define: {
    "process.env.NODE_ENV": '"production"', // Inject environment variables
  },
});
