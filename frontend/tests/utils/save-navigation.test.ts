import { afterEach, describe, expect, it, vi } from "vitest";

import { completeCreateOrEditNavigation } from "@/utils/save-navigation";

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("create or edit save navigation", () => {
  it("returns to the existing detail page after an edit", () => {
    const navigateBack = vi.fn();
    const redirectTo = vi.fn();
    vi.stubGlobal("uni", { navigateBack, redirectTo });

    completeCreateOrEditNavigation({
      isEditMode: true,
      detailUrl: "/pages/tasks/detail?task_id=task-1",
    });

    expect(navigateBack).toHaveBeenCalledTimes(1);
    expect(navigateBack.mock.calls[0]?.[0]).toEqual(
      expect.objectContaining({ fail: expect.any(Function) }),
    );
    expect(redirectTo).not.toHaveBeenCalled();
  });

  it("falls back to the detail route when an edit page has no previous page", () => {
    const redirectTo = vi.fn();
    const navigateBack = vi.fn((options: { fail?: () => void }) => options.fail?.());
    vi.stubGlobal("uni", { navigateBack, redirectTo });

    completeCreateOrEditNavigation({
      isEditMode: true,
      detailUrl: "/pages/supplies/detail?supply_point_id=supply-1",
    });

    expect(redirectTo).toHaveBeenCalledWith({
      url: "/pages/supplies/detail?supply_point_id=supply-1",
    });
  });

  it("replaces a create page with the newly created detail page", () => {
    const navigateBack = vi.fn();
    const redirectTo = vi.fn();
    vi.stubGlobal("uni", { navigateBack, redirectTo });

    completeCreateOrEditNavigation({
      isEditMode: false,
      detailUrl: "/pages/landmarks/detail?landmark_id=landmark-1",
    });

    expect(redirectTo).toHaveBeenCalledWith({
      url: "/pages/landmarks/detail?landmark_id=landmark-1",
    });
    expect(navigateBack).not.toHaveBeenCalled();
  });
});
