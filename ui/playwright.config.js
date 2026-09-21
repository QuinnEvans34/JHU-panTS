import { defineConfig } from '@playwright/test'

export default defineConfig({
  testDir: './tests/browser',
  outputDir: '../outputs/prowl/testing/ui-browser',
  fullyParallel: false, workers: 1, retries: 0,
  use: { browserName: 'chromium', baseURL: 'http://127.0.0.1:5179', trace: 'retain-on-failure', screenshot: 'only-on-failure' },
  webServer: {
    command: 'npm run test:fixture', url: 'http://127.0.0.1:5179',
    reuseExistingServer: false, timeout: 30000,
  },
})
