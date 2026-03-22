import { test, expect } from '@playwright/test';
import path from 'path';

const authFile = path.join(__dirname, '.auth/admin.json');

test.use({ storageState: authFile });

test.describe('Masters / Verifications page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/masters');
    await page.waitForLoadState('networkidle', { timeout: 15000 }).catch(() => {});
  });

  test('masters page loads without application error', async ({ page }) => {
    const bodyText = await page.locator('body').textContent();
    expect(bodyText).not.toContain('Application error');
    expect(bodyText).not.toContain('client-side exception');
  });

  test('page has "Masters" heading', async ({ page }) => {
    const heading = await page.locator('h1').first().textContent();
    expect(heading?.toLowerCase()).toContain('masters');
  });

  test('tabs are visible: All, Pending, Verified, Rejected', async ({ page }) => {
    await page.waitForSelector('[role="tablist"]', { timeout: 10000 });
    const tabs = await page.locator('[role="tab"]').allTextContents();
    const tabText = tabs.join(' ').toLowerCase();
    expect(tabText).toContain('all');
    expect(tabText).toContain('pending');
    expect(tabText).toContain('verified');
    expect(tabText).toContain('rejected');
  });

  test('pending tab shows verifications (2 pending exist)', async ({ page }) => {
    // Click Pending tab
    await page.locator('[role="tab"]:has-text("Pending")').click();
    await page.waitForLoadState('networkidle', { timeout: 10000 }).catch(() => {});
    await page.waitForSelector('tbody tr', { timeout: 10000 });

    const rows = await page.locator('tbody tr').count();
    expect(rows).toBeGreaterThanOrEqual(1);

    // Status column should contain "pending" badges
    const bodyText = await page.locator('tbody').textContent();
    expect(bodyText?.toLowerCase()).toContain('pending');
  });

  test('each master row has a visible name', async ({ page }) => {
    await page.waitForSelector('tbody tr', { timeout: 10000 });
    const rows = page.locator('tbody tr');
    const count = await rows.count();
    expect(count).toBeGreaterThan(0);

    // First data row (not "no verifications" row)
    const firstCell = await rows.first().locator('td').first().textContent();
    // Should be a name or "No verifications found"
    expect(firstCell?.trim().length).toBeGreaterThan(0);
  });

  test('pending masters have approve and reject buttons', async ({ page }) => {
    await page.locator('[role="tab"]:has-text("Pending")').click();
    await page.waitForLoadState('networkidle', { timeout: 10000 }).catch(() => {});
    await page.waitForSelector('tbody tr td', { timeout: 10000 });

    const bodyText = await page.locator('tbody').textContent();
    if (bodyText?.includes('No verifications')) {
      test.skip(); // No pending verifications
      return;
    }

    // First pending row
    const firstRow = page.locator('tbody tr').first();
    // Approve button (check icon) and Reject button (X icon) should be visible
    await expect(firstRow.locator('button[title="Approve"]')).toBeVisible();
    await expect(firstRow.locator('button[title="Reject"]')).toBeVisible();
  });

  test('eye/view button opens master detail dialog', async ({ page }) => {
    await page.waitForSelector('tbody tr td', { timeout: 10000 });

    const bodyText = await page.locator('tbody').textContent();
    if (bodyText?.includes('No verifications')) {
      test.skip();
      return;
    }

    const firstRow = page.locator('tbody tr').first();
    await firstRow.locator('button[title="View details"]').click();

    await expect(page.locator('[role="dialog"]')).toBeVisible({ timeout: 5000 });
    const dialogText = await page.locator('[role="dialog"]').textContent();
    expect(dialogText?.toLowerCase()).toMatch(/master details|verification/i);
  });

  test('detail dialog shows verification info (name, status)', async ({ page }) => {
    await page.waitForSelector('tbody tr td', { timeout: 10000 });

    const bodyText = await page.locator('tbody').textContent();
    if (bodyText?.includes('No verifications')) {
      test.skip();
      return;
    }

    const firstRow = page.locator('tbody tr').first();
    await firstRow.locator('button[title="View details"]').click();

    await expect(page.locator('[role="dialog"]')).toBeVisible({ timeout: 5000 });
    // Dialog should show Name and Status labels
    const dialogText = await page.locator('[role="dialog"]').textContent();
    expect(dialogText?.toLowerCase()).toContain('name');
    expect(dialogText?.toLowerCase()).toContain('status');
  });

  test('reject button opens rejection reason dialog', async ({ page }) => {
    await page.locator('[role="tab"]:has-text("Pending")').click();
    await page.waitForLoadState('networkidle', { timeout: 10000 }).catch(() => {});
    await page.waitForSelector('tbody tr td', { timeout: 10000 });

    const bodyText = await page.locator('tbody').textContent();
    if (bodyText?.includes('No verifications')) {
      test.skip();
      return;
    }

    const firstRow = page.locator('tbody tr').first();
    await firstRow.locator('button[title="Reject"]').click();

    await expect(page.locator('[role="dialog"]')).toBeVisible({ timeout: 5000 });
    const dialogText = await page.locator('[role="dialog"]').textContent();
    expect(dialogText?.toLowerCase()).toContain('reject');
  });

  test('rejection dialog has input field and Cancel/Reject buttons', async ({ page }) => {
    await page.locator('[role="tab"]:has-text("Pending")').click();
    await page.waitForLoadState('networkidle', { timeout: 10000 }).catch(() => {});
    await page.waitForSelector('tbody tr td', { timeout: 10000 });

    const bodyText = await page.locator('tbody').textContent();
    if (bodyText?.includes('No verifications')) {
      test.skip();
      return;
    }

    await page.locator('tbody tr').first().locator('button[title="Reject"]').click();
    await expect(page.locator('[role="dialog"]')).toBeVisible({ timeout: 5000 });

    // Input field for rejection reason
    await expect(page.locator('[role="dialog"] input[placeholder*="reason"], [role="dialog"] input')).toBeVisible();

    // Cancel button
    await expect(page.locator('[role="dialog"] button:has-text("Cancel")')).toBeVisible();

    // Reject button (destructive)
    await expect(page.locator('[role="dialog"] button:has-text("Reject")')).toBeVisible();

    // Close without rejecting
    await page.locator('[role="dialog"] button:has-text("Cancel")').click();
    await expect(page.locator('[role="dialog"]')).not.toBeVisible({ timeout: 5000 });
  });

  test('all tab shows all verifications', async ({ page }) => {
    await page.locator('[role="tab"]:has-text("All")').click();
    await page.waitForLoadState('networkidle', { timeout: 10000 }).catch(() => {});
    await page.waitForSelector('tbody', { timeout: 10000 });

    // Should show table (even if empty)
    await expect(page.locator('table')).toBeVisible();
  });
});
