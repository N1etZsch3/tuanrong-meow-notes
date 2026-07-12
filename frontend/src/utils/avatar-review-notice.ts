export type AvatarReviewStatus = "idle" | "pending" | "passed" | "rejected" | "failed";

interface AvatarReviewNoticeStorage {
  getStorageSync: (key: string) => unknown;
  setStorageSync: (key: string, value: unknown) => void;
}

const FAILURE_NOTICE_PREFIX = "catmap:avatar-review-failure";

export function consumeAvatarReviewFailureNotice(
  ownerId: string,
  assetId: string | null | undefined,
  status: AvatarReviewStatus,
  storage: AvatarReviewNoticeStorage = uni,
): boolean {
  if (!ownerId || !assetId || !["rejected", "failed"].includes(status)) {
    return false;
  }

  const key = `${FAILURE_NOTICE_PREFIX}:${ownerId}:${assetId}:${status}`;
  try {
    if (storage.getStorageSync(key)) {
      return false;
    }
    storage.setStorageSync(key, true);
  } catch {
    return true;
  }
  return true;
}
