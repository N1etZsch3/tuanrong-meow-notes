import { describe, expect, it } from "vitest";

import appSource from "../../src/App.vue?raw";
import adminUsersSource from "../../src/pages/admin/users/index.vue?raw";
import catsSource from "../../src/pages/cats/index.vue?raw";
import landmarksSource from "../../src/pages/landmarks/index.vue?raw";
import medicinesHoldingSource from "../../src/pages/medicines/holding.vue?raw";
import medicinesSource from "../../src/pages/medicines/index.vue?raw";
import messagesSource from "../../src/pages/messages/index.vue?raw";
import profileNotificationsSource from "../../src/pages/profile/notifications.vue?raw";
import profileRecordsSource from "../../src/pages/profile/records.vue?raw";
import publicCatsSource from "../../src/pages/public/cats.vue?raw";
import suppliesSource from "../../src/pages/supplies/index.vue?raw";
import tasksSource from "../../src/pages/tasks/list.vue?raw";

function firstVerticalScrollTag(source: string): string {
  const tag = source
    .match(/<scroll-view[\s\S]*?>/g)
    ?.find((candidate) => /\bscroll-y\b/.test(candidate));
  expect(tag).toBeDefined();
  return tag || "";
}

describe("list page scrollbars", () => {
  it("uses enhanced scroll views with hidden vertical scrollbars on every list page", () => {
    const listPages = [
      adminUsersSource,
      catsSource,
      landmarksSource,
      medicinesHoldingSource,
      medicinesSource,
      messagesSource,
      profileNotificationsSource,
      profileRecordsSource,
      publicCatsSource,
      suppliesSource,
      tasksSource,
    ];

    for (const source of listPages) {
      const scrollTag = firstVerticalScrollTag(source);
      expect(scrollTag).toContain("enhanced");
      expect(scrollTag).toContain(':show-scrollbar="false"');
    }
  });

  it("keeps a global WebView scrollbar fallback for all scroll views", () => {
    expect(appSource).toContain("scroll-view::-webkit-scrollbar");
    expect(appSource).toContain("scrollbar-width: none");
    expect(appSource).toContain("color: transparent");
  });
});
