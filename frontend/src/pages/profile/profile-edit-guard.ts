export interface ProfileEditSnapshot {
  nickname: string;
  department: string;
  contact_info: string;
  avatar_url: string | null;
}

export function createProfileEditSnapshot(
  profile: ProfileEditSnapshot,
): ProfileEditSnapshot {
  return {
    nickname: profile.nickname.trim(),
    department: profile.department,
    contact_info: profile.contact_info.trim(),
    avatar_url: profile.avatar_url || null,
  };
}

export function hasUnsavedProfileChanges(
  saved: ProfileEditSnapshot | null,
  current: ProfileEditSnapshot,
): boolean {
  if (!saved) {
    return false;
  }

  const normalizedCurrent = createProfileEditSnapshot(current);
  return (
    saved.nickname !== normalizedCurrent.nickname ||
    saved.department !== normalizedCurrent.department ||
    saved.contact_info !== normalizedCurrent.contact_info ||
    saved.avatar_url !== normalizedCurrent.avatar_url
  );
}
