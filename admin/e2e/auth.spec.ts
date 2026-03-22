import { test, expect } from '@playwright/test';

test.describe('Authentication', () => {
  test('should login and redirect to dashboard', async ({ page }) => {
    await page.goto('/login');
    await page.fill('input[type="email"]', 'admin@local.ru');
    await page.fill('input[type="password"]', 'Admin123');
    await page.click('button[type="submit"]');
    await page.waitForURL('**/dashboard', { timeout: 15000 });
    expect(page.url()).toContain('/dashboard');
  });

  test('should redirect to login when accessing dashboard without auth', async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForURL('**/login**', { timeout: 15000 });
    expect(page.url()).toContain('/login');
  });
});
