interface CompleteCreateOrEditNavigationOptions {
  isEditMode: boolean;
  detailUrl: string;
}

export function completeCreateOrEditNavigation({
  isEditMode,
  detailUrl,
}: CompleteCreateOrEditNavigationOptions): void {
  if (!isEditMode) {
    uni.redirectTo({ url: detailUrl });
    return;
  }

  uni.navigateBack({
    fail: () => {
      uni.redirectTo({ url: detailUrl });
    },
  });
}
