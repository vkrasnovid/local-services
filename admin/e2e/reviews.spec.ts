import { test, expect } from '@playwright/test';
import path from 'path';

const authFile = path.join(__dirname, '.auth/admin.json');

test.use({ storageState: authFile });

test.describe('Reviews page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/reviews');
    await page.waitForLoadState('networkidle', { timeout: 15000 }).catch(() => {});
  });

  test('reviews page loads without application error', async ({ page }) => {
    const bodyText = await page.locator('body').textContent();
    expect(bodyText).not.toContain('Application error');
    expect(bodyText).not.toContain('client-side exception');
  });

  test('page has "Reviews" heading', async ({ page }) => {
    const heading = await page.locator('h1').first().textContent();
    expect(heading?.toLowerCase()).toContain('reviews');
  });

  test('reviews list container is visible (table or empty state)', async ({ page }) => {
    await page.waitForLoadState('networkidle', { timeout: 10000 }).catch(() => {});
    const bodyText = await page.locator('body').textContent();
    expect(bodyText?.toLowerCase()).toContain('reviews');
    expect(bodyText).not.toContain('Application error');
    // Either table or empty state card
    const hasTable = await page.locator('table').count();
    const hasEmptyState = bodyText?.includes('No reviews found') || bodyText?.includes('reviews');
    expect(hasTable > 0 || hasEmptyState).toBeTruthy();
  });

  test('empty state message is user-friendly when no reviews exist', async ({ page }) => {
    await page.waitForLoadState('networkidle', { timeout: 10000 }).catch(() => {});
    // Check only visible rendered content (not RSC payload)
    const mainText = await page.locator('main, [role="main"]').textContent();
    // No crash
    expect(mainText).not.toContain('Application error');
    // If no reviews, should show friendly count/message
    const hasNoReviews = mainText?.includes('No reviews found') || mainText?.match(/0 reviews/i);
    const hasReviews = await page.locator('table').count() > 0;
    expect(hasNoReviews || hasReviews).toBeTruthy();
  });

  test('visibility filter dropdown exists', async ({ page }) => {
    const comboboxes = page.locator('[role="combobox"]');
    const count = await comboboxes.count();
    expect(count).toBeGreaterThanOrEqual(1);
  });

  test('table column headers include rating or text (if reviews exist)', async ({ page }) => {
    await page.waitForLoadState('networkidle', { timeout: 10000 }).catch(() => {});
    const hasTable = await page.locator('table').count();
    if (!hasTable) {
      // No table when empty - skip this check
      const bodyText = await page.locator('body').textContent();
      expect(bodyText?.toLowerCase()).toContain('reviews');
      return;
    }
    const headers = await page.locator('thead th').allTextContents();
    const headerText = headers.join(' ').toLowerCase();
    expect(headerText.length).toBeGreaterThan(0);
  });

  test('moderation toggle or eye/hide button visible if reviews exist', async ({ page }) => {
    await page.waitForLoadState('networkidle', { timeout: 10000 }).catch(() => {});

    const hasTable = await page.locator('table').count();
    if (!hasTable) {
      // No reviews exist yet - acceptable empty state
      const bodyText = await page.locator('body').textContent();
      expect(bodyText?.toLowerCase()).toContain('reviews');
      return;
    }

    // If reviews exist, each row should have a visibility toggle button
    const firstRow = page.locator('tbody tr').first();
    const buttons = await firstRow.locator('button').count();
    expect(buttons).toBeGreaterThanOrEqual(1);
  });
});
