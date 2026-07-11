export const STARTUP_PROGRESS_INITIAL = 12;
export const STARTUP_PROGRESS_WAITING_LIMIT = 92;

export function advanceStartupProgress(currentProgress: number): number {
  const normalizedProgress = Math.max(
    0,
    Math.min(STARTUP_PROGRESS_WAITING_LIMIT, Math.round(currentProgress)),
  );

  if (normalizedProgress >= STARTUP_PROGRESS_WAITING_LIMIT) {
    return STARTUP_PROGRESS_WAITING_LIMIT;
  }

  const step = normalizedProgress < 60 ? 4 : normalizedProgress < 80 ? 2 : 1;
  return Math.min(STARTUP_PROGRESS_WAITING_LIMIT, normalizedProgress + step);
}
