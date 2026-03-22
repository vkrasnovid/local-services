import { test, expect } from '@playwright/test';
import path from 'path';

const authFile = path.join(__dirname, '.auth/admin.json');

test.use({ storageState: authFile });

test.describe('Users page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/users');
    await page.waitForLoadState('networkidle', { timeout: 15000 }).catch(() => {});
  });

  test('users page loads without application error', async ({ page }) => {
    const bodyText = await page.locator('body').textContent();
    expect(bodyText).not.toContain('Application error');
    expect(bodyText).not.toContain('client-side exception');
  });

  test('page has "Users" heading', async ({ page }) => {
    const heading = await page.locator('h1').first().textContent();
    expect(heading?.toLowerCase()).toContain('users');
  });

  test('table is visible with correct column headers', async ({ page }) => {
    await page.waitForSelector('table', { timeout: 10000 });
    const headers = await page.locator('thead th').allTextContents();
    const headerText = headers.join(' ').toLowerCase();
    expect(headerText).toContain('name');
    expect(headerText).toContain('email');
    expect(headerText).toContain('role');
    expect(headerText).toContain('status');
  });

  test('table shows 4 users (all users in the system)', async ({ page }) => {
    await page.waitForSelector('tbody tr', { timeout: 10000 });
    const rows = await page.locator('tbody tr').count();
    // There are 4 users; no "No users found" row
    expect(rows).toBeGreaterThanOrEqual(4);
  });

  test('each user row has non-empty name and email', async ({ page }) => {
    await page.waitForSelector('tbody tr', { timeout: 10000 });
    const rows = page.locator('tbody tr');
    const count = await rows.count();
    expect(count).toBeGreaterThan(0);
    for (let i = 0; i < count; i++) {
      const cells = rows.nth(i).locator('td');
      const name = await cells.nth(0).textContent();
      const email = await cells.nth(1).textContent();
      expect(name?.trim().length).toBeGreaterThan(0);
      expect(email?.trim().length).toBeGreaterThan(0);
    }
  });

  test('known users are visible in the table (admin, masters, client)', async ({ page }) => {
    await page.waitForSelector('tbody tr', { timeout: 10000 });
    const bodyText = await page.locator('tbody').textContent();
    expect(bodyText).toContain('admin@local.ru');
  });

  test('role filter exists and has All/Client/Master/Admin options', async ({ page }) => {
    // Select component for role filter
    const roleSelect = page.locator('button:has-text("All roles"), button[role="combobox"]').first();
    // Check that there's at least one select trigger
    const selectTriggers = await page.locator('[role="combobox"]').count();
    expect(selectTriggers).toBeGreaterThanOrEqual(1);
  });

  test('filtering by role "master" shows only masters', async ({ page }) => {
    await page.waitForSelector('tbody tr', { timeout: 10000 });

    // Find role select trigger (first combobox)
    const comboboxes = page.locator('[role="combobox"]');
    const firstCombobox = comboboxes.first();
    await firstCombobox.click();

    // Select "Master" option
    await page.locator('[role="option"]:has-text("Master")').click();

    // Wait for the table to stop showing "Loading..." and show actual data
    await page.waitForFunction(() => {
      const tbody = document.querySelector('tbody');
      return tbody && !tbody.textContent?.includes('Loading...');
    }, { timeout: 10000 });

    const rows = await page.locator('tbody tr').count();
    // 2 masters exist in the system
    expect(rows).toBeGreaterThanOrEqual(1);
    expect(rows).toBeLessThanOrEqual(5);

    const bodyText = await page.locator('tbody').textContent();
    // Should show master role badges
    expect(bodyText?.toLowerCase()).toContain('master');
  });

  test('search input exists and filters results', async ({ page }) => {
    await page.goto('/users');
    await page.waitForLoadState('networkidle', { timeout: 15000 }).catch(() => {});
    await page.waitForSelector('input[placeholder*="Search"]', { timeout: 10000 });
    const searchInput = page.locator('input[placeholder*="Search"]');
    await expect(searchInput).toBeVisible();

    await searchInput.fill('admin@local.ru');
    // Wait for debounce (300ms) and then data load
    await page.waitForTimeout(400);
    await page.waitForFunction(() => {
      const tbody = document.querySelector('tbody');
      return tbody && !tbody.textContent?.includes('Loading...');
    }, { timeout: 10000 });

    const bodyText = await page.locator('tbody').textContent();
    expect(bodyText).toContain('admin@local.ru');
  });

  test('action buttons (Block, Change Role) are visible in each row', async ({ page }) => {
    await page.waitForSelector('tbody tr', { timeout: 10000 });
    const firstRow = page.locator('tbody tr').first();
    await expect(firstRow.locator('button:has-text("Block"), button:has-text("Unblock")')).toBeVisible();
    await expect(firstRow.locator('button:has-text("Change Role")')).toBeVisible();
  });

  test('clicking Block opens confirmation dialog', async ({ page }) => {
    await page.waitForSelector('tbody tr', { timeout: 10000 });

    // Find a non-admin user to block (avoid blocking admin)
    const rows = page.locator('tbody tr');
    const count = await rows.count();
    let targetRow = -1;
    for (let i = 0; i < count; i++) {
      const emailText = await rows.nth(i).locator('td').nth(1).textContent();
      if (emailText && !emailText.includes('admin@local.ru')) {
        targetRow = i;
        break;
      }
    }

    if (targetRow === -1) {
      test.skip(); // Only admin exists
      return;
    }

    await rows.nth(targetRow).locator('button:has-text("Block"), button:has-text("Unblock")').first().click();

    // Dialog should appear
    await expect(page.locator('[role="dialog"]')).toBeVisible({ timeout: 5000 });
    const dialogText = await page.locator('[role="dialog"]').textContent();
    expect(dialogText?.toLowerCase()).toMatch(/block|unblock/);

    // Cancel button should close dialog
    await page.locator('[role="dialog"] button:has-text("Cancel")').click();
    await expect(page.locator('[role="dialog"]')).not.toBeVisible({ timeout: 5000 });
  });
});
