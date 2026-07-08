import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  forbidOnly: !!process.env.CI,
  use: { baseURL: "http://127.0.0.1:3000", trace: "on-first-retry" },
  webServer: [
    {
      command: "node e2e/mock-dashboard-api.mjs",
      url: "http://127.0.0.1:3100/health",
      reuseExistingServer: !process.env.CI,
    },
    {
      command: "CHURN_API_BASE_URL=http://127.0.0.1:3100 pnpm dev --hostname 127.0.0.1 --port 3000",
      url: "http://127.0.0.1:3000",
      reuseExistingServer: !process.env.CI,
    },
  ],
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
});
