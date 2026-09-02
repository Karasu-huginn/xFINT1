import { defineConfig } from "vitest/config";

// Kept apart from vite.config.ts on purpose. Vitest bundles its own copy of Vite,
// so a single config that imports both a Vite plugin and vitest/config makes
// tsc compare two different Vite type trees and fail on identical shapes.
export default defineConfig({
  test: {
    environment: "node",
    include: ["src/**/*.test.ts"],
  },
});
