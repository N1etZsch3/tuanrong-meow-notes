import { describe, expect, it } from "vitest";

import {
  DEFAULT_STATE_PRESETS,
  DEFAULT_TAB_PAGE_STATES,
  getDefaultStatePreset,
  type DefaultStateKey,
} from "@/components/default-state";
import defaultStateSource from "@/components/DefaultState.vue?raw";

describe("default state presets", () => {
  it("provides common reusable default states", () => {
    const expectedKeys: DefaultStateKey[] = [
      "under_development",
      "empty_data",
      "empty_records",
      "empty_search",
      "network_error",
      "permission_denied",
      "not_found",
      "empty_location",
      "image_error",
      "empty_messages",
    ];

    expect(Object.keys(DEFAULT_STATE_PRESETS)).toEqual(expectedKeys);
  });

  it("uses the prepared default-state illustrations", () => {
    expect(
      decodeURI(getDefaultStatePreset("under_development").illustration),
    ).toContain("正在紧急开发.svg");
    expect(decodeURI(getDefaultStatePreset("empty_records").illustration)).toContain(
      "记录空空的.svg",
    );
    expect(decodeURI(getDefaultStatePreset("network_error").illustration)).toContain(
      "网络加载异常.svg",
    );
  });

  it("maps current tab placeholders to the under-development state", () => {
    expect(DEFAULT_TAB_PAGE_STATES).toEqual({
      map: "under_development",
      cats: "under_development",
      tasks: "under_development",
      profile: "under_development",
    });
  });

  it("falls back to empty data when an unknown state is requested", () => {
    expect(getDefaultStatePreset("missing" as DefaultStateKey).key).toBe(
      "empty_data",
    );
  });

  it("uses the shared lowered heading metrics for full-page defaults", () => {
    expect(defaultStateSource).toContain("var(--catmap-page-title-top, 92rpx)");
    expect(defaultStateSource).toContain("font-size: var(--catmap-page-title-font-size, 52rpx)");
    expect(defaultStateSource).toContain("font-size: var(--catmap-page-title-subtitle-size, 24rpx)");
    expect(defaultStateSource).not.toContain("padding: 64rpx 34rpx 44rpx");
    expect(defaultStateSource).not.toContain("font-size: 60rpx");
  });
});
