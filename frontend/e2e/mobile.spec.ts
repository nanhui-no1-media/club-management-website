import { test, expect } from "@playwright/test";

const MOBILE = {
  userAgent:
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
  viewport: { width: 390, height: 844 },
  hasTouch: true,
  isMobile: true,
} as const;

test.describe("移动版（匿名）", () => {
  test.use({ ...MOBILE, storageState: { cookies: [], origins: [] } });

  test("访问首页自动跳转手机版并渲染", async ({ page }) => {
    await page.goto("/");
    await expect(page).toHaveURL(/#\/m$/);
    await expect(page.locator(".m-app")).toBeVisible();
  });
});

test.describe("移动版（登录）", () => {
  test.use({ ...MOBILE });

  test("四个页面渲染；我的页显示身份与后台入口", async ({ page }) => {
    await page.goto("/#/m");
    await expect(page.locator(".m-app")).toBeVisible();

    await page.goto("/#/m/news");
    await expect(page.locator(".m-app")).toBeVisible();
    await expect(page.getByText("E2E 种子新闻").first()).toBeVisible({ timeout: 10_000 });

    await page.goto("/#/m/activity");
    await expect(page.locator(".m-app")).toBeVisible();

    await page.goto("/#/m/me");
    await expect(page.locator(".m-app")).toBeVisible();
    await expect(page.getByText("E2E 信息员")).toBeVisible({ timeout: 10_000 });
    await expect(page.getByText("@e2e_info")).toBeVisible();
    await expect(page.getByText("进入后台管理")).toBeVisible();
  });
});
