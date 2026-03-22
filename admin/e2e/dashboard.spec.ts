import { test, expect } from '@playwright/test';
import path from 'path';

const authFile = path.join(__dirname, '.auth/admin.json');

test.use({ storageState: authFile });

test.describe('Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForLoadState('domcontentloaded');
  });

  test('should have Dashboard in page title or heading', async ({ page }) => {
    const heading = await page.locator('h1').first().textContent();
    expect(heading?.toLowerCase()).toContain('dashboard');
  });

  test('should not show application error', async ({ page }) => {
    await page.waitForLoadState('networkidle', { timeout: 15000 }).catch(() => {});
    const bodyText = await page.locator('body').textContent();
    expect(bodyText).not.toContain('Application error');
    expect(bodyText).not.toContain('client-side exception');
  });

  test('should have at least one stat card visible', async ({ page }) => {
    await page.waitForSelector('.grid .shadow-sm', { timeout: 15000 });
    const cards = await page.locator('.grid .shadow-sm').count();
    expect(cards).toBeGreaterThanOrEqual(1);
  });
});
