export interface MemberEditSnapshot {
  nickname: string;
  real_name: string;
  departments: string[];
  grade: string;
  contact_info: string;
  role: string;
  status: string;
  avatar_url: string | null;
}

export function createMemberEditSnapshot(
  member: MemberEditSnapshot,
): MemberEditSnapshot {
  return {
    nickname: member.nickname.trim(),
    real_name: member.real_name.trim(),
    departments: [...member.departments],
    grade: member.grade.trim(),
    contact_info: member.contact_info.trim(),
    role: member.role,
    status: member.status,
    avatar_url: member.avatar_url || null,
  };
}

export function hasUnsavedMemberChanges(
  saved: MemberEditSnapshot | null,
  current: MemberEditSnapshot,
): boolean {
  if (!saved) {
    return false;
  }

  const normalizedCurrent = createMemberEditSnapshot(current);
  return (
    saved.nickname !== normalizedCurrent.nickname ||
    saved.real_name !== normalizedCurrent.real_name ||
    saved.departments.join("|") !== normalizedCurrent.departments.join("|") ||
    saved.grade !== normalizedCurrent.grade ||
    saved.contact_info !== normalizedCurrent.contact_info ||
    saved.role !== normalizedCurrent.role ||
    saved.status !== normalizedCurrent.status ||
    saved.avatar_url !== normalizedCurrent.avatar_url
  );
}
