import { defineConfig, type Plugin } from "vite";
import react from "@vitejs/plugin-react";

const removeLocalhostFallbacks = (): Plugin => ({
  name: "remove-localhost-fallbacks",
  apply: "build",
  generateBundle(_, bundle) {
    for (const asset of Object.values(bundle)) {
      if (asset.type === "chunk") {
        asset.code = asset.code.replaceAll("http://localhost", "https://recruteur.talentsag.ma");
      }
    }
  },
});

export default defineConfig({
  plugins: [react(), removeLocalhostFallbacks()],
});
