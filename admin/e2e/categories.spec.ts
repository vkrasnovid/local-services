import { test, expect } from '@playwright/test';
import path from 'path';

const authFile = path.join(__dirname, '.auth/admin.json');

test.use({ storageState: authFile });

test.describe('Categories page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/categories');
    await page.waitForLoadState('networkidle', { timeout: 15000 }).catch(() => {});
  });

  test('categories page loads without application error', async ({ page }) => {
    const bodyText = await page.locator('body').textContent();
    expect(bodyText).not.toContain('Application error');
    expect(bodyText).not.toContain('client-side exception');
  });

  test('page has "Categories" heading', async ({ page }) => {
    const heading = await page.locator('h1').first().textContent();
    expect(heading?.toLowerCase()).toContain('categories');
  });

  test('table shows categories (Уборка and Ремонт should be visible)', async ({ page }) => {
    await page.waitForSelector('tbody tr', { timeout: 10000 });
    const bodyText = await page.locator('tbody').textContent();
    // At least one of the known categories
    const hasKnownCategories =
      bodyText?.includes('Уборка') || bodyText?.includes('Ремонт') || bodyText?.includes('уборка');
    expect(hasKnownCategories).toBeTruthy();
  });

  test('each category row has name and slug columns', async ({ page }) => {
    await page.waitForSelector('tbody tr', { timeout: 10000 });
    const headers = await page.locator('thead th').allTextContents();
    const headerText = headers.join(' ').toLowerCase();
    expect(headerText).toContain('name');
    expect(headerText).toContain('slug');
  });

  test('each category row has non-empty name and slug', async ({ page }) => {
    await page.waitForSelector('tbody tr', { timeout: 10000 });
    const rows = page.locator('tbody tr');
    const count = await rows.count();
    expect(count).toBeGreaterThan(0);

    for (let i = 0; i < Math.min(count, 3); i++) {
      const cells = rows.nth(i).locator('td');
      // Name is td[1] (index 1, after icon at 0)
      const name = await cells.nth(1).textContent();
      const slug = await cells.nth(2).textContent();
      expect(name?.trim().length).toBeGreaterThan(0);
      expect(slug?.trim().length).toBeGreaterThan(0);
    }
  });

  test('"Add Category" button exists', async ({ page }) => {
    await expect(page.locator('button:has-text("Add Category")')).toBeVisible();
  });

  test('clicking "Add Category" opens form dialog', async ({ page }) => {
    await page.locator('button:has-text("Add Category")').click();
    await expect(page.locator('[role="dialog"]')).toBeVisible({ timeout: 5000 });
    const dialogText = await page.locator('[role="dialog"]').textContent();
    expect(dialogText?.toLowerCase()).toContain('add category');
  });

  test('add category form has name and slug fields', async ({ page }) => {
    await page.locator('button:has-text("Add Category")').click();
    await expect(page.locator('[role="dialog"]')).toBeVisible({ timeout: 5000 });

    await expect(page.locator('[role="dialog"] input#name, [role="dialog"] input[id="name"]')).toBeVisible();
    await expect(page.locator('[role="dialog"] input#slug, [role="dialog"] input[id="slug"]')).toBeVisible();
  });

  test('cancel button closes dialog without saving', async ({ page }) => {
    await page.locator('button:has-text("Add Category")').click();
    await expect(page.locator('[role="dialog"]')).toBeVisible({ timeout: 5000 });

    await page.locator('[role="dialog"] button:has-text("Cancel")').click();
    await expect(page.locator('[role="dialog"]')).not.toBeVisible({ timeout: 5000 });
  });

  test('create new category with unique name appears in table', async ({ page }) => {
    const uniqueName = `TestCat-${Date.now()}`;
    const uniqueSlug = `test-cat-${Date.now()}`;

    await page.locator('button:has-text("Add Category")').click();
    await expect(page.locator('[role="dialog"]')).toBeVisible({ timeout: 5000 });

    await page.locator('[role="dialog"] input#name').fill(uniqueName);
    await page.locator('[role="dialog"] input#slug').fill(uniqueSlug);

    await page.locator('[role="dialog"] button[type="submit"]').click();
    await page.waitForLoadState('networkidle', { timeout: 10000 }).catch(() => {});

    // Dialog should close
    await expect(page.locator('[role="dialog"]')).not.toBeVisible({ timeout: 5000 });

    // New category should appear in the table
    await page.waitForSelector(`td:has-text("${uniqueName}")`, { timeout: 10000 });
    const bodyText = await page.locator('tbody').textContent();
    expect(bodyText).toContain(uniqueName);
  });

  test('edit existing category opens dialog with pre-filled values', async ({ page }) => {
    await page.waitForSelector('tbody tr', { timeout: 10000 });

    // Click edit button (pencil icon) on first row
    const firstRow = page.locator('tbody tr').first();
    const categoryName = await firstRow.locator('td').nth(1).textContent();

    await firstRow.locator('button').nth(0).click(); // Edit button (first action button)
    await expect(page.locator('[role="dialog"]')).toBeVisible({ timeout: 5000 });

    // Check pre-filled name
    const nameInput = page.locator('[role="dialog"] input#name');
    const nameValue = await nameInput.inputValue();
    expect(nameValue.length).toBeGreaterThan(0);
    // Should match the category name from the row
    expect(nameValue).toBe(categoryName?.trim());
  });

  test('delete button opens confirmation dialog', async ({ page }) => {
    await page.waitForSelector('tbody tr', { timeout: 10000 });

    // Click delete button (trash icon) on first row — second action button
    const firstRow = page.locator('tbody tr').first();
    await firstRow.locator('button').nth(1).click(); // Delete button

    await expect(page.locator('[role="dialog"]')).toBeVisible({ timeout: 5000 });
    const dialogText = await page.locator('[role="dialog"]').textContent();
    expect(dialogText?.toLowerCase()).toContain('delete');

    // Cancel to not actually delete
    await page.locator('[role="dialog"] button:has-text("Cancel")').click();
    await expect(page.locator('[role="dialog"]')).not.toBeVisible({ timeout: 5000 });
  });
});
