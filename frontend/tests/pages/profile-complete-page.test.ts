import { describe, expect, test } from "vitest";

import profileCompleteVue from "../../src/pages/profile/complete.vue?raw";
import { normalizeInitialProfileText } from "../../src/pages/profile/complete-page";

describe("profile completion page", () => {
  test("does not render the optional bottom tip card", () => {
    expect(profileCompleteVue).not.toContain("tip-card");
    expect(profileCompleteVue).not.toContain("小提示");
  });

  test("normalizes question-mark placeholders to empty initial form values", () => {
    expect(normalizeInitialProfileText("????")).toBe("");
    expect(normalizeInitialProfileText("?????")).toBe("");
    expect(normalizeInitialProfileText("  ????  ")).toBe("");
    expect(normalizeInitialProfileText("喂猫搭子🥜")).toBe("喂猫搭子🥜");
    expect(normalizeInitialProfileText(null)).toBe("");
  });
});
