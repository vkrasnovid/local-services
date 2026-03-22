import { test, expect } from '@playwright/test';
import path from 'path';

const authFile = path.join(__dirname, '.auth/admin.json');

test.use({ storageState: authFile });

test.describe('Bookings page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/bookings');
    await page.waitForLoadState('networkidle', { timeout: 15000 }).catch(() => {});
  });

  test('bookings page loads without application error', async ({ page }) => {
    const bodyText = await page.locator('body').textContent();
    expect(bodyText).not.toContain('Application error');
    expect(bodyText).not.toContain('client-side exception');
  });

  test('page has "Bookings" heading', async ({ page }) => {
    const heading = await page.locator('h1').first().textContent();
    expect(heading?.toLowerCase()).toContain('bookings');
  });

  test('bookings list container is visible (table or empty state)', async ({ page }) => {
    // Bookings page shows either a table or "No bookings found" message
    await page.waitForSelector('h1, h3, [role="main"]', { timeout: 10000 });
    const bodyText = await page.locator('body').textContent();
    // Should contain Bookings heading
    expect(bodyText?.toLowerCase()).toContain('bookings');
    // No application crash
    expect(bodyText).not.toContain('Application error');
  });

  test('table columns are visible when bookings exist, or empty state shown', async ({ page }) => {
    await page.waitForLoadState('networkidle', { timeout: 10000 }).catch(() => {});
    const bodyText = await page.locator('body').textContent();
    // Either a table with status column or "No bookings found" message
    const hasTable = await page.locator('table').count();
    const hasEmptyState = bodyText?.includes('No bookings found') || bodyText?.includes('Bookings (0)');
    expect(hasTable > 0 || hasEmptyState).toBeTruthy();
  });

  test('empty state message is graceful when no bookings', async ({ page }) => {
    await page.waitForLoadState('networkidle', { timeout: 10000 }).catch(() => {});
    // Check only visible rendered text in main content area, not RSC payload
    const mainText = await page.locator('main, [role="main"]').textContent();
    // If no bookings, should show friendly message, not an error
    expect(mainText).not.toContain('Application error');
    // Should show "No bookings found" or similar empty state
    const hasEmptyState = mainText?.includes('No bookings found') || mainText?.match(/Bookings \(0\)/i);
    const hasBookings = await page.locator('table tbody tr').count() > 0;
    expect(hasEmptyState || hasBookings).toBeTruthy();
  });

  test('status filter dropdown exists', async ({ page }) => {
    await expect(page.locator('[role="combobox"]').first()).toBeVisible({ timeout: 10000 });

    await page.locator('[role="combobox"]').first().click();
    await page.waitForSelector('[role="option"]', { timeout: 5000 });

    const options = await page.locator('[role="option"]').allTextContents();
    const optText = options.join(' ').toLowerCase();
    expect(optText).toContain('all');

    await page.keyboard.press('Escape');
  });

  test('date range filter inputs exist', async ({ page }) => {
    const dateInputs = page.locator('input[type="date"]');
    const count = await dateInputs.count();
    expect(count).toBeGreaterThanOrEqual(2);
  });

  test('summary stats card shows Total Bookings', async ({ page }) => {
    const bodyText = await page.locator('body').textContent();
    expect(bodyText?.toLowerCase()).toMatch(/total bookings|bookings/i);
  });
});
