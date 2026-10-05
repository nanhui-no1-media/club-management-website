import { afterEach, describe, expect, it } from "vitest";
import { isMobileDevice } from "../device";

const setUA = (ua: string) =>
  Object.defineProperty(window.navigator, "userAgent", { value: ua, configurable: true });

describe("isMobileDevice", () => {
  const original = window.navigator.userAgent;
  afterEach(() => setUA(original));

  it("手机 UA（iPhone / Android）命中", () => {
    setUA("Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1");
    expect(isMobileDevice()).toBe(true);

    setUA("Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Mobile Safari/537.36");
    expect(isMobileDevice()).toBe(true);
  });

  it("桌面 UA 不命中", () => {
    setUA("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36");
    expect(isMobileDevice()).toBe(false);
  });
});
