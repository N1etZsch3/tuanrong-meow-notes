import { describe, expect, it } from "vitest";

import loadingPageSource from "../../src/pages/loading/index.vue?raw";
import {
  advanceStartupProgress,
  STARTUP_PROGRESS_INITIAL,
  STARTUP_PROGRESS_WAITING_LIMIT,
} from "@/pages/loading/loading-page";

describe("loading page", () => {
  it("uses the approved prototype assets and layout copy", () => {
    expect(loadingPageSource).toContain("背景.jpg");
    expect(loadingPageSource).toContain("团绒猫.png");
    expect(loadingPageSource).toContain("团绒喵记本字标.png");
    expect(loadingPageSource).toContain("记录每一次温暖的相遇");
    expect(loadingPageSource).toContain('role="progressbar"');
    expect(loadingPageSource).not.toContain("加载页会徽.png");
    expect(loadingPageSource).not.toContain("麦穗1.svg");
    expect(loadingPageSource).not.toContain("团绒猫.webp");
    expect(loadingPageSource).not.toContain("团绒喵记本字标.jpg");
    expect(loadingPageSource).not.toContain("paw-loader");
  });

  it("keeps the prototype elements at compact mobile proportions", () => {
    expect(loadingPageSource).toContain("width: 360rpx");
    expect(loadingPageSource).toContain("height: 310rpx");
    expect(loadingPageSource).toContain("width: 460rpx");
    expect(loadingPageSource).toContain("height: 110rpx");
    expect(loadingPageSource).toContain("width: 270rpx");
    expect(loadingPageSource).toContain("font-size: 26rpx");
  });

  it("keeps progress below completion until startup resolves", () => {
    let progress = STARTUP_PROGRESS_INITIAL;
    const observedProgress = [progress];

    for (let index = 0; index < 100; index += 1) {
      progress = advanceStartupProgress(progress);
      observedProgress.push(progress);
    }

    expect(
      observedProgress.every(
        (value) => value <= STARTUP_PROGRESS_WAITING_LIMIT,
      ),
    ).toBe(true);
    expect(observedProgress[observedProgress.length - 1]).toBe(
      STARTUP_PROGRESS_WAITING_LIMIT,
    );
    expect(
      observedProgress
        .slice(1)
        .every((value, index) => value >= observedProgress[index]),
    ).toBe(true);
  });

  it("reaches the prototype-like middle state after the initial animation", () => {
    let progress = STARTUP_PROGRESS_INITIAL;

    for (let index = 0; index < 16; index += 1) {
      progress = advanceStartupProgress(progress);
    }

    expect(progress).toBe(68);
  });

  it("completes the visual progress only after resolving the startup route", () => {
    const resolveRouteIndex = loadingPageSource.indexOf(
      "resolveStartupRoute(userStore)",
    );
    const completeProgressIndex = loadingPageSource.indexOf(
      "await completeLoadingProgress()",
    );
    const navigateIndex = loadingPageSource.indexOf("await navigateTo(route)");

    expect(resolveRouteIndex).toBeGreaterThanOrEqual(0);
    expect(completeProgressIndex).toBeGreaterThan(resolveRouteIndex);
    expect(navigateIndex).toBeGreaterThan(completeProgressIndex);
    expect(loadingPageSource).toContain("loadingProgress.value = 100");
    expect(loadingPageSource).toContain("stopProgressAnimation()");
  });
});
