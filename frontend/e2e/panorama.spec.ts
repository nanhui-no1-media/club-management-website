import { expect, test } from "@playwright/test";
import type { Page } from "@playwright/test";
import { uniqueTitle } from "./utils";

/**
 * 在真实浏览器里现画一张 256×128（严格 2:1）JPEG。
 *
 * 特意不内联长 base64 常量：那种字符串抄错一个字符就变成「不是图片」，
 * 报错却在后端、很难定位；canvas.toDataURL 由浏览器保证产出合法 JPEG。
 * （既有 320×200 PNG 是 1.6:1，会被后端的 2:1 准入规则拒掉，不能复用。）
 */
async function makePanoramaJpeg(page: Page): Promise<Buffer> {
  const dataUrl = (await page.evaluate(() => {
    const canvas = document.createElement("canvas");
    canvas.width = 256;
    canvas.height = 128;
    const ctx = canvas.getContext("2d");
    if (ctx) {
      ctx.fillStyle = "#1c3a68";
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      for (let i = 0; i < 8; i += 1) {
        ctx.fillStyle = `hsl(${i * 40}, 55%, ${35 + i * 5}%)`;
        ctx.fillRect((canvas.width / 8) * i, 0, canvas.width / 16, canvas.height);
      }
    }
    return canvas.toDataURL("image/jpeg", 0.8);
  })) as string;
  return Buffer.from(dataUrl.split(",")[1], "base64");
}

/**
 * 校园全景图冒烟：管理页导入 → 浏览页取瓦片。
 *
 * 注意：全站是 hash 路由，页面地址必须写成 `/#/...`；写成 `/panorama/...` 会被
 * Django 的 `panorama/` 路由（/config/urls.py 已把该前缀从 SPA catch-all 里排除）
 * 接走，根本进不了 SPA。
 *
 * 前置：`e2e_info` 在 seed_e2e 里是超管（is_superuser=True），故持有
 * `panorama.manage_panoramas`；E2E 每个 run 重建数据库，库内初始为空，
 * 因而导入的这一张就是浏览页的当前（也是唯一）场景。
 */
test.describe("校园全景图", () => {
  test("导入后浏览页能取到瓦片，且取片模板未被百分号转义", async ({ page }) => {
    // 本用例比其它 UI 用例重：传图 → 服务端同步切片 → 加载 3D 渲染器 → 取瓦片，
    // 默认 30s 只够「点几下」，这里显式放宽；下面的断言仍然逐条硬性生效。
    test.setTimeout(90_000);

    const title = uniqueTitle("E2E 全景");
    const tiles: { url: string; status: number }[] = [];
    page.on("response", (res) => {
      const url = res.url();
      if (url.includes("/media/panorama/tiles/")) {
        tiles.push({ url, status: res.status() });
      }
    });

    // ── 1. 管理页导入（服务端同步切片；256×128 小图毫秒级）───────────
    await page.goto("/#/panorama/manage");
    await expect(page.getByRole("heading", { name: "管理校园全景图" })).toBeVisible();
    // 导入表单存在 = 能力门禁已放行（否则渲染的是无权限面板）
    await expect(page.getByRole("heading", { name: "导入全景图" })).toBeVisible();

    // SPA 启动时才拉取 csrftoken cookie（App 的 useEffect → GET /auth/csrf/）。
    // 不等它就提交，首次 POST 会被 Django 的 CSRF 校验挡下（403）。
    await page.waitForFunction(() => document.cookie.includes("csrftoken"));

    await page.setInputFiles('input[type="file"]', {
      name: "e2e-panorama.jpg",
      mimeType: "image/jpeg",
      buffer: await makePanoramaJpeg(page),
    });
    await page.getByPlaceholder("如：操场").fill(title);
    await page.getByRole("button", { name: "导入并切片" }).click();

    await expect(page.getByText(/已导入/)).toBeVisible({ timeout: 30_000 });
    // 列表里出现该条目（库内只有一张，可直接定位徒标标题）
    await expect(page.locator(".pano-card-head strong")).toHaveText(title, { timeout: 10_000 });

    // ── 2. 浏览页：库内仅此一张，它就是当前场景 ────────────────────
    await page.goto("/#/panorama");
    await expect(page.getByRole("heading", { name: title })).toBeVisible({ timeout: 15_000 });

    // ── 3. 瓦片必须真的取到 200；URL 不得出现被转义的占位符 ───────
    //    （build_absolute_uri 会把 {z} 转成 %7Bz%7D，Marzipano 就再也换不上占位符）
    //    不断言具体渲染舞台：headless 有无 WebGL 会让 WebGL / CSS 两条路不同。
    await expect
      .poll(() => tiles.length, { timeout: 30_000, message: "等不到瓦片请求" })
      .toBeGreaterThan(0);

    const ok = tiles.filter((t) => t.status === 200);
    expect(ok.length, `瓦片响应：${JSON.stringify(tiles)}`).toBeGreaterThan(0);
    expect(
      tiles.some((t) => t.url.includes("%7B")),
      `取片模板被百分号转义，前端换不上占位符：${JSON.stringify(tiles.slice(0, 3))}`,
    ).toBe(false);
  });
});
