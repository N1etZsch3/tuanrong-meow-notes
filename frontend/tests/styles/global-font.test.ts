import { describe, expect, test } from "vitest";

import appVue from "../../src/App.vue?raw";
import agents from "../../../AGENTS.md?raw";

const fontStack = '"Songti SC", "STSong", "SimSun"';

describe("global Chinese font rules", () => {
  test("applies the Songti font stack from the app root", () => {
    expect(appVue).toContain(`font-family: ${fontStack}`);
  });

  test("records Songti as the frontend typography standard", () => {
    expect(agents).toContain("中文字体");
    expect(agents).toContain(fontStack);
  });

  test("records mobile WeChat viewport as the frontend layout baseline", () => {
    expect(agents).toContain("微信小程序视口");
    expect(agents).toContain("手机");
  });

  test("keeps shared page title metrics and loading background rule", () => {
    expect(appVue).toContain("--catmap-page-title-top: 92rpx");
    expect(appVue).toContain("--catmap-page-title-side: 42rpx");
    expect(appVue).toContain("--catmap-page-title-gap: 14rpx");
    expect(appVue).toContain("--catmap-page-title-font-size: 52rpx");
    expect(appVue).toContain("--catmap-page-title-icon-size: 48rpx");
    expect(appVue).toContain("--catmap-page-title-subtitle-margin: 14rpx");
    expect(appVue).toContain("--catmap-page-title-subtitle-size: 24rpx");
    expect(agents).toContain("frontend/素材/加载页素材/加载页背景.jpg");
  });
});
