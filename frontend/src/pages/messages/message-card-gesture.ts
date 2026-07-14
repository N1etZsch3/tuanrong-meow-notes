export type CardGestureIntent =
  | "pending"
  | "horizontal"
  | "vertical"
  | "longpress"
  | "consumed";

export interface CardGesturePoint {
  x: number;
  y: number;
  touchId?: number;
}

export interface CardGestureState {
  messageId: string;
  startX: number;
  startY: number;
  lastX: number;
  lastY: number;
  touchId: number | null;
  intent: CardGestureIntent;
  didMove: boolean;
  startedOpen: boolean;
}

export interface CardGestureUpdate {
  state: CardGestureState;
  deltaX: number;
  deltaY: number;
}

export interface CardInteractionSnapshot {
  gestureActive: boolean;
  longPressPending: boolean;
  menuOpen: boolean;
  swipeOpen: boolean;
  swipeDragging: boolean;
}

export interface CardRefreshGuardSnapshot {
  gestureIntent: CardGestureIntent | null;
  longPressPending: boolean;
  menuOpen: boolean;
  swipeOpen: boolean;
  swipeDragging: boolean;
}

/** Small finger jitter is still a valid long press. */
export const LONG_PRESS_SLOP_PX = 5;

/** Wait for a deliberate move before locking the gesture axis. */
export const DIRECTION_LOCK_DISTANCE_PX = 8;

const AXIS_LOCK_RATIO = 1.15;
const AMBIGUOUS_DIRECTION_DISTANCE_PX = 16;

function distanceFromStart(state: CardGestureState, point: CardGesturePoint): number {
  const deltaX = point.x - state.startX;
  const deltaY = point.y - state.startY;
  return Math.sqrt(deltaX * deltaX + deltaY * deltaY);
}

export function startCardGesture(
  messageId: string,
  point: CardGesturePoint,
  options: { consume?: boolean; startedOpen?: boolean } = {},
): CardGestureState {
  return {
    messageId,
    startX: point.x,
    startY: point.y,
    lastX: point.x,
    lastY: point.y,
    touchId: point.touchId ?? null,
    intent: options.consume ? "consumed" : "pending",
    didMove: false,
    startedOpen: Boolean(options.startedOpen),
  };
}

export function isCardGestureOwner(
  state: CardGestureState | null,
  messageId: string,
  touchId?: number,
): boolean {
  if (!state || state.messageId !== messageId) {
    return false;
  }
  return state.touchId === null || touchId === undefined || state.touchId === touchId;
}

export function shouldDeferMessageListUpdate(snapshot: CardInteractionSnapshot): boolean {
  return (
    snapshot.gestureActive ||
    snapshot.longPressPending ||
    snapshot.menuOpen ||
    snapshot.swipeOpen ||
    snapshot.swipeDragging
  );
}

export function shouldBlockMessageRefresh(snapshot: CardRefreshGuardSnapshot): boolean {
  return (
    snapshot.gestureIntent === "horizontal" ||
    snapshot.gestureIntent === "longpress" ||
    snapshot.gestureIntent === "consumed" ||
    snapshot.longPressPending ||
    snapshot.menuOpen ||
    snapshot.swipeOpen ||
    snapshot.swipeDragging
  );
}

export function updateCardGesture(
  state: CardGestureState,
  point: CardGesturePoint,
): CardGestureUpdate {
  const deltaX = point.x - state.startX;
  const deltaY = point.y - state.startY;
  const absX = Math.abs(deltaX);
  const absY = Math.abs(deltaY);
  const distance = distanceFromStart(state, point);
  let intent = state.intent;

  if (intent === "pending") {
    const crossedDirectionThreshold =
      absX >= DIRECTION_LOCK_DISTANCE_PX || absY >= DIRECTION_LOCK_DISTANCE_PX;

    if (crossedDirectionThreshold) {
      if (absX >= absY * AXIS_LOCK_RATIO) {
        intent = "horizontal";
      } else if (absY >= absX * AXIS_LOCK_RATIO) {
        intent = "vertical";
      } else if (Math.max(absX, absY) >= AMBIGUOUS_DIRECTION_DISTANCE_PX) {
        intent = absX >= absY ? "horizontal" : "vertical";
      }
    }
  }

  return {
    state: {
      ...state,
      lastX: point.x,
      lastY: point.y,
      intent,
      didMove: state.didMove || distance > LONG_PRESS_SLOP_PX,
    },
    deltaX,
    deltaY,
  };
}

export function canActivateCardLongPress(
  state: CardGestureState | null,
  messageId: string,
  eventPoint?: CardGesturePoint | null,
): boolean {
  if (!state || state.messageId !== messageId || state.intent !== "pending" || state.didMove) {
    return false;
  }
  return eventPoint ? distanceFromStart(state, eventPoint) <= LONG_PRESS_SLOP_PX : true;
}

export function activateCardLongPress(state: CardGestureState): CardGestureState {
  return {
    ...state,
    intent: "longpress",
  };
}

export function shouldSuppressCardTap(state: CardGestureState | null): boolean {
  return Boolean(state && (state.intent !== "pending" || state.didMove));
}
