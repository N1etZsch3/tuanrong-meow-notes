import { describe, expect, it } from "vitest";

import pagesJson from "../../src/pages.json?raw";
import notesIndexSource from "../../src/pages/tasks/index.vue?raw";
import helpFeedbackSource from "../../src/pages/profile/help-feedback.vue?raw";
import {
  HELP_CONTACT_ITEMS,
  HELP_FAQ_ITEMS,
} from "../../src/pages/profile/help-feedback";

describe("meow notes shelf", () => {
  it("keeps the five record books on the first shelf page", () => {
    expect(notesIndexSource).toContain("/pages/tasks/list");
    expect(notesIndexSource).toContain("/pages/supplies/index");
    expect(notesIndexSource).toContain("/pages/landmarks/index");
    expect(notesIndexSource).toContain("/pages/medicines/index");
    expect(notesIndexSource).toContain("/pages/cats/index");
    expect(notesIndexSource).toContain("RECORD_BOOKS");
  });

  it("adds an admin-only manage shelf page pointing at personnel management", () => {
    expect(notesIndexSource).toContain("ADMIN_BOOKS");
    expect(notesIndexSource).toContain("/pages/admin/users/index");
    expect(notesIndexSource).toContain("useUserStore");
    expect(notesIndexSource).toContain("userStore.isAdmin");
    expect(notesIndexSource).toContain('subtitle: "记录入口"');
    expect(notesIndexSource).toContain('subtitle: "管理入口"');
  });

  it("switches the header subtitle with the active shelf page", () => {
    expect(notesIndexSource).toContain("currentShelfSubtitle");
    expect(notesIndexSource).toContain('{{ currentShelfSubtitle }}');
    expect(notesIndexSource).not.toContain("记录与管理入口");
  });

  it("hides the shelf pager when only one page is available to non-admins", () => {
    expect(notesIndexSource).toContain("showShelfPager");
    expect(notesIndexSource).toContain('v-if="showShelfPager"');
    expect(notesIndexSource).toContain("totalBookPages.value > 1");
  });

  it("clamps the active shelf page so a vanished admin page never shows empty", () => {
    expect(notesIndexSource).toContain("activeBookPage");
    expect(notesIndexSource).toContain("Math.min(currentBookPage.value, totalBookPages.value - 1)");
    expect(notesIndexSource).toContain("onShow");
  });
});

describe("help and feedback page", () => {
  it("registers the help-feedback route", () => {
    expect(pagesJson).toContain("pages/profile/help-feedback");
  });

  it("renders static FAQ and contact content without a backend call", () => {
    expect(HELP_FAQ_ITEMS.length).toBeGreaterThan(0);
    expect(HELP_CONTACT_ITEMS.length).toBeGreaterThan(0);
    expect(helpFeedbackSource).toContain("HELP_FAQ_ITEMS");
    expect(helpFeedbackSource).toContain("HELP_CONTACT_ITEMS");
    expect(helpFeedbackSource).toContain("常见问题");
    expect(helpFeedbackSource).toContain("联系我们");
    expect(helpFeedbackSource).not.toContain("request(");
    expect(helpFeedbackSource).toContain("var(--catmap-page-title-top, 92rpx)");
  });
});
