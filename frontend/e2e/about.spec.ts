import { test, expect } from "@playwright/test";

test("关于页：标题、区块目录与种子内容渲染", async ({ page }) => {
  await page.goto("/#/about");

  await expect(page.getByRole("heading", { name: "关于我们", level: 1 })).toBeVisible();
  await expect(page.getByRole("navigation", { name: "关于区块" })).toBeVisible();

  // 区块默认折叠：展开「社团简介」后可见种子正文
  await page.getByRole("button", { name: "社团简介" }).click();
  await expect(page.getByText("E2E 社团简介正文。")).toBeVisible();
});
