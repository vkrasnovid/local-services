import { chromium } from '@playwright/test';

async function globalSetup() {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();

  await page.goto('http://217.114.5.77:3000/login');
  await page.fill('input[type="email"]', 'admin@local.ru');
  await page.fill('input[type="password"]', 'Admin123');
  await page.click('button[type="submit"]');
  await page.waitForURL('**/dashboard', { timeout: 15000 });

  // Save storage state (cookies + localStorage)
  await page.context().storageState({ path: 'e2e/.auth/admin.json' });
  await browser.close();
}

export default globalSetup;
