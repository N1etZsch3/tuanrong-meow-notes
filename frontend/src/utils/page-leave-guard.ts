export type PageLeaveRequest = "leave" | "confirm" | "blocked";

type PageLeaveGuardState = "ready" | "confirming" | "allowed";

export interface PageLeaveGuard {
  requestLeave: () => PageLeaveRequest;
  confirmDiscard: () => boolean;
  cancelDiscard: () => void;
  reset: () => void;
}

export function createPageLeaveGuard(
  hasUnsavedChanges: () => boolean,
): PageLeaveGuard {
  let state: PageLeaveGuardState = "ready";

  return {
    requestLeave() {
      if (state === "allowed") {
        return "leave";
      }
      if (state === "confirming") {
        return "blocked";
      }
      if (hasUnsavedChanges()) {
        state = "confirming";
        return "confirm";
      }
      state = "allowed";
      return "leave";
    },
    confirmDiscard() {
      if (state !== "confirming") {
        return false;
      }
      state = "allowed";
      return true;
    },
    cancelDiscard() {
      if (state === "confirming") {
        state = "ready";
      }
    },
    reset() {
      state = "ready";
    },
  };
}
