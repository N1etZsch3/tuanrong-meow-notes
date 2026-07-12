export type PageLeaveRequest = "leave" | "confirm" | "blocked";
export type PageLeaveOrigin = "button" | "container";
export type PageContainerLeaveAction = "navigate" | "rearm";

type PageLeaveGuardState = "ready" | "confirming" | "allowed";

export interface PageLeaveGuard {
  requestLeave: () => PageLeaveRequest;
  confirmDiscard: () => boolean;
  cancelDiscard: () => void;
  reset: () => void;
}

export interface PageContainerLeaveResolution {
  closeContainer: boolean;
  action: PageContainerLeaveAction | null;
}

export interface PageContainerLeaveCoordinator {
  begin: (origin: PageLeaveOrigin) => void;
  resolve: (action: PageContainerLeaveAction) => PageContainerLeaveResolution;
  afterContainerLeave: () => PageContainerLeaveAction | null;
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

export function createPageContainerLeaveCoordinator(): PageContainerLeaveCoordinator {
  let origin: PageLeaveOrigin | null = null;
  let containerHasLeft = false;
  let pendingAction: PageContainerLeaveAction | null = null;

  function reset() {
    origin = null;
    containerHasLeft = false;
    pendingAction = null;
  }

  return {
    begin(nextOrigin) {
      origin = nextOrigin;
      containerHasLeft = false;
      pendingAction = null;
    },
    resolve(action) {
      if (origin === null) {
        return { closeContainer: false, action };
      }
      if (origin === "button" && action === "rearm") {
        reset();
        return { closeContainer: false, action: null };
      }
      if (containerHasLeft) {
        reset();
        return { closeContainer: false, action };
      }

      pendingAction = action;
      return {
        closeContainer: origin === "button" && action === "navigate",
        action: null,
      };
    },
    afterContainerLeave() {
      containerHasLeft = true;
      if (!pendingAction) {
        return null;
      }
      const action = pendingAction;
      reset();
      return action;
    },
    reset,
  };
}
