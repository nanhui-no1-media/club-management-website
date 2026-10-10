import { expect, test } from "@playwright/test";
import { panoramaBuffer, uniqueTitle } from "./utils";

/**
 * 校园全景图冒烟：管理页导入 → 浏览页取瓦片。
 *
 * 前置：`e2e_info` 在 seed_e2e 里是超管（is_superuser=True），故持有
 * `panorama.manage_panoramas`；E2E 每个 run 重建数据库，库内初始为空，
 * 因而导入的这一张就是浏览页的当前（也是唯一）场景。
 */
test.describe("校园全景图", () => {
  test("导入后浏览页能取到瓦片，且取片模板未被百分号转义", async ({ page }) => {
    const title = uniqueTitle("E2E 全景");
    const tiles: { url: string; status: number }[] = [];
    page.on("response", (res) => {
      const url = res.url();
      if (url.includes("/media/panorama/tiles/")) {
        tiles.push({ url, status: res.status() });
      }
    });

    // ── 1. 管理页导入（服务端同步切片；128×64 小图毫秒级）──────────────
    await page.goto("/panorama/manage");
    await expect(page.getByRole("heading", { name: "管理校园全景图" })).toBeVisible();

    await page.setInputFiles('input[type="file"]', {
      name: "e2e-panorama.jpg",
      mimeType: "image/jpeg",
      buffer: panoramaBuffer(),
    });
    await page.getByPlaceholder("如：操场").fill(title);
    await page.getByRole("button", { name: "导入并切片" }).click();

    await expect(page.getByText(/已导入/)).toBeVisible({ timeout: 20_000 });
    // 列表里出现该条目（库内只有一张，可直接定位徒标标题）
    await expect(page.locator(".pano-card-head strong")).toHaveText(title);

    // ── 2. 浏览页：库内仅此一张，它就是当前场景 ─────────────────────
    await page.goto("/panorama");
    await expect(page.getByRole("heading", { name: title })).toBeVisible();

    // 场景建成（WebGL 或回落 CSS 舞台均可）后，加载遮罩会消失
    await expect(page.locator(".pano-overlay")).toHaveCount(0, { timeout: 20_000 });

    // ── 3. 瓦片必须真的取到 200；URL 里不得出现被转义的占位符 ──────
    //    （build_absolute_uri 会把 {z} 转成 %7Bz%7D，Marzipano 就再也换不上占位符）
    await expect
      .poll(() => tiles.length, { timeout: 20_000, message: "等不到瓦片请求" })
      .toBeGreaterThan(0);

    const ok = tiles.filter((t) => t.status === 200);
    expect(ok.length, `瓦片响应：${JSON.stringify(tiles)}`).toBeGreaterThan(0);
    expect(
      tiles.some((t) => t.url.includes("%7B")),
      `取片模板被百分号转义，前端换不上占位符：${JSON.stringify(tiles.slice(0, 3))}`,
    ).toBe(false);
  });
});
