import { afterEach, describe, expect, it, vi } from "vitest";

import { returnToListAfterDelete } from "@/utils/delete-navigation";

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("delete navigation", () => {
  it("returns to an existing list page and removes deleted detail pages from the stack", () => {
    const navigateBack = vi.fn();
    const reLaunch = vi.fn();
    vi.stubGlobal("uni", { navigateBack, reLaunch });
    vi.stubGlobal("getCurrentPages", () => [
      { route: "pages/tasks/index" },
      { route: "pages/tasks/list" },
      { route: "pages/tasks/detail" },
      { route: "pages/admin/tasks/create" },
    ]);

    returnToListAfterDelete("/pages/tasks/list");

    expect(navigateBack).toHaveBeenCalledWith({ delta: 2 });
    expect(reLaunch).not.toHaveBeenCalled();
  });

  it("relaunches the requested list when it is not present in the page stack", () => {
    const navigateBack = vi.fn();
    const reLaunch = vi.fn();
    vi.stubGlobal("uni", { navigateBack, reLaunch });
    vi.stubGlobal("getCurrentPages", () => [
      { route: "pages/index/index" },
      { route: "pages/landmarks/detail" },
      { route: "pages/admin/landmarks/create" },
    ]);

    returnToListAfterDelete("/pages/landmarks/index");

    expect(reLaunch).toHaveBeenCalledWith({ url: "/pages/landmarks/index" });
    expect(navigateBack).not.toHaveBeenCalled();
  });
});
