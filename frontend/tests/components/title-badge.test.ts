import { describe, expect, it } from "vitest";

import titleBadgeSource from "../../src/components/TitleBadge.vue?raw";
import {
  TITLE_DEFINITIONS,
  getTitleDefinition,
} from "../../src/constants/titles";

describe("title badge", () => {
  it("defines twelve unique title identities across three shield variants", () => {
    expect(TITLE_DEFINITIONS).toHaveLength(12);
    expect(new Set(TITLE_DEFINITIONS.map((item) => item.key)).size).toBe(12);
    expect(new Set(TITLE_DEFINITIONS.map((item) => item.tag_background)).size).toBe(12);
    expect(new Set(TITLE_DEFINITIONS.map((item) => item.shield))).toEqual(
      new Set(["gold", "purple", "green"]),
    );
    expect(getTitleDefinition("president")?.label).toBe("会长");
    expect(getTitleDefinition(null)).toBeNull();
  });

  it("renders a reusable shield and label while hiding an empty title", () => {
    expect(titleBadgeSource).toContain('v-if="definition"');
    expect(titleBadgeSource).toContain("definition.label");
    expect(titleBadgeSource).toContain("shieldAssets");
    expect(titleBadgeSource).toContain('font-family: "Songti SC"');
  });
});
