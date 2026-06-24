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
});
