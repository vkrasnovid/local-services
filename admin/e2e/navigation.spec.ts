import { test, expect } from '@playwright/test';
import path from 'path';

const authFile = path.join(__dirname, '.auth/admin.json');

test.use({ storageState: authFile });

test.describe('Navigation / Sidebar', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle', { timeout: 15000 }).catch(() => {});
  });

  test('sidebar is visible on desktop', async ({ page }) => {
    // Default viewport is desktop
    await expect(page.locator('nav')).toBeVisible({ timeout: 10000 });
  });

  test('all nav links are present in sidebar', async ({ page }) => {
    const navLinks = ['Dashboard', 'Users', 'Masters', 'Bookings', 'Transactions', 'Reviews', 'Categories'];
    for (const linkName of navLinks) {
      await expect(page.locator(`nav a:has-text("${linkName}")`)).toBeVisible({ timeout: 5000 });
    }
  });

  test('clicking Dashboard nav link navigates to /dashboard', async ({ page }) => {
    await page.locator('nav a:has-text("Dashboard")').click();
    await page.waitForURL('**/dashboard', { timeout: 10000 });
    expect(page.url()).toContain('/dashboard');
  });

  test('clicking Users nav link navigates to /users', async ({ page }) => {
    await page.locator('nav a:has-text("Users")').click();
    await page.waitForURL('**/users', { timeout: 10000 });
    expect(page.url()).toContain('/users');
  });

  test('clicking Masters nav link navigates to /masters', async ({ page }) => {
    await page.locator('nav a:has-text("Masters")').click();
    await page.waitForURL('**/masters', { timeout: 10000 });
    expect(page.url()).toContain('/masters');
  });

  test('clicking Categories nav link navigates to /categories', async ({ page }) => {
    await page.locator('nav a:has-text("Categories")').click();
    await page.waitForURL('**/categories', { timeout: 10000 });
    expect(page.url()).toContain('/categories');
  });

  test('clicking Bookings nav link navigates to /bookings', async ({ page }) => {
    await page.locator('nav a:has-text("Bookings")').click();
    await page.waitForURL('**/bookings', { timeout: 10000 });
    expect(page.url()).toContain('/bookings');
  });

  test('clicking Transactions nav link navigates to /transactions', async ({ page }) => {
    await page.locator('nav a:has-text("Transactions")').click();
    await page.waitForURL('**/transactions', { timeout: 10000 });
    expect(page.url()).toContain('/transactions');
  });

  test('clicking Reviews nav link navigates to /reviews', async ({ page }) => {
    await page.locator('nav a:has-text("Reviews")').click();
    await page.waitForURL('**/reviews', { timeout: 10000 });
    expect(page.url()).toContain('/reviews');
  });

  test('active nav link has highlighted/active styling', async ({ page }) => {
    // Dashboard should be active on /dashboard
    const dashboardLink = page.locator('nav a:has-text("Dashboard")');
    const className = await dashboardLink.getAttribute('class');
    // Active class should contain bg-primary or text-primary
    expect(className).toMatch(/primary|active/i);
  });

  test('logout button exists in sidebar', async ({ page }) => {
    // Logout button in sidebar bottom
    const logoutBtn = page.locator('button[title="Logout"], button:has([class*="LogOut"]), button:has(svg)');
    // The sidebar footer area has a logout button
    const sidebarFooter = page.locator('aside, div[class*="sidebar"], div[class*="flex flex-col"]').last();

    // Look for logout button with title attribute
    await expect(page.locator('button[title="Logout"]')).toBeVisible({ timeout: 10000 });
  });

  test('hamburger menu button is visible at narrow viewport (375px)', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 812 });
    await page.reload();
    await page.waitForLoadState('networkidle', { timeout: 10000 }).catch(() => {});

    // Hamburger button should be visible on mobile
    await expect(page.locator('button[aria-label="Open menu"]')).toBeVisible({ timeout: 5000 });
  });

  test('hamburger button opens sidebar on mobile', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 812 });
    await page.reload();
    await page.waitForLoadState('networkidle', { timeout: 10000 }).catch(() => {});

    const hamburger = page.locator('button[aria-label="Open menu"]');
    await hamburger.click();

    // Sidebar should slide in
    await expect(page.locator('nav a:has-text("Dashboard")')).toBeVisible({ timeout: 5000 });
  });
});
