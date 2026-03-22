import { test, expect } from '@playwright/test';
import path from 'path';

const authFile = path.join(__dirname, '.auth/admin.json');

test.use({ storageState: authFile });

const SECTIONS = ['users', 'masters', 'bookings', 'transactions', 'reviews', 'categories'];

test.describe('Sections load without errors', () => {
  for (const section of SECTIONS) {
    test(`/${section} loads without application error`, async ({ page }) => {
      await page.goto(`/${section}`, { waitUntil: 'domcontentloaded', timeout: 10000 });
      await page.waitForLoadState('networkidle', { timeout: 10000 }).catch(() => {
        // Ignore timeout on networkidle – some pages have long-running requests
      });

      const bodyText = await page.locator('body').textContent();
      expect(bodyText).not.toContain('Application error');
      expect(bodyText).not.toContain('client-side exception');
    });
  }
});
