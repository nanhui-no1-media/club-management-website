import { test, expect } from "@playwright/test";

// 手机 UA + 触屏视口：访问首页应自动进入手机版
test.use({
  userAgent:
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
  viewport: { width: 390, height: 844 },
  hasTouch: true,
  isMobile: true,
  storageState: { cookies: [], origins: [] },
});

test("移动端：首页自动跳转手机版并渲染", async ({ page }) => {
  await page.goto("/");
  await expect(page).toHaveURL(/#\/m$/);
  await expect(page.locator(".m-app")).toBeVisible();
});
