const { defineConfig } = require("@playwright/test");

module.exports = defineConfig({
  testDir: "./tests/javascript",
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: 0,
  workers: process.env.CI ? 2 : undefined,
  reporter: "list",
  use: {
    browserName: "chromium",
    viewport: { width: 1000, height: 600 },
    trace: "retain-on-failure",
  },
});
