import { describe, expect, it } from "vitest";

import titleBadgeSource from "../../src/components/TitleBadge.vue?raw";
import titleIdentityNameSource from "../../src/components/TitleIdentityName.vue?raw";
import titleShieldAssetsSource from "../../src/components/title-shield-assets.ts?raw";
import { DEPARTMENT_THEMES } from "../../src/constants/departments";
import {
  TITLE_DEFINITIONS,
  getTitleDefinition,
} from "../../src/constants/titles";

describe("title badge", () => {
  it("defines twelve semantic title identities with department-based palettes", () => {
    expect(TITLE_DEFINITIONS).toHaveLength(12);
    expect(new Set(TITLE_DEFINITIONS.map((item) => item.key)).size).toBe(12);
    expect(new Set(TITLE_DEFINITIONS.map((item) => item.shield_asset)).size).toBe(12);
    expect(new Set(TITLE_DEFINITIONS.map((item) => item.name_color)).size).toBe(12);
    expect(new Set(TITLE_DEFINITIONS.map((item) => item.shield))).toEqual(
      new Set(["gold", "purple", "green"]),
    );
    expect(getTitleDefinition("president")?.label).toBe("会长");
    expect(getTitleDefinition("president")?.name_color).toBe("#a52828");
    expect(getTitleDefinition("vice_president")?.name_color).toBe("#8a6817");
    expect(getTitleDefinition("survival_head")?.name_color).toBe(
      DEPARTMENT_THEMES.生存保障部.head_title,
    );
    expect(getTitleDefinition("survival_deputy")?.name_color).toBe(
      DEPARTMENT_THEMES.生存保障部.deputy_title,
    );
    expect(getTitleDefinition("survival_head")?.tag_background).toBe(
      getTitleDefinition("survival_deputy")?.tag_background,
    );
    expect(getTitleDefinition(null)).toBeNull();
  });

  it("maps each semantic title color to its badge and colored member name", () => {
    expect(titleBadgeSource).toContain('v-if="definition"');
    expect(titleBadgeSource).toContain("definition.label");
    expect(titleBadgeSource).toContain("TITLE_SHIELD_ASSETS[definition.shield_asset]");
    expect(titleIdentityNameSource).toContain("TITLE_SHIELD_ASSETS[definition.shield_asset]");
    expect(titleShieldAssetsSource.match(/盾牌-.*?\.svg/g)).toHaveLength(12);
    expect(titleIdentityNameSource).toContain("definition?.name_color");
    expect(titleIdentityNameSource).not.toContain("definition.label");
    expect(titleIdentityNameSource).toContain("width: 100%");
    expect(titleIdentityNameSource).toContain("text-overflow: ellipsis");
    expect(titleBadgeSource).toContain('font-family: "Songti SC"');
  });
});
