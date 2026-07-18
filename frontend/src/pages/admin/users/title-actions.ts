import type { TitleCatalogItem } from "@/api/titles";

export function availableAssignableTitles(
  items: TitleCatalogItem[],
  targetUserId: string,
): TitleCatalogItem[] {
  return items.filter(
    (item) =>
      item.key !== "president" &&
      (item.is_available || item.holder?.user_id === targetUserId),
  );
}

export function canManageMemberTitles(
  currentRole: string | null | undefined,
  currentTitle: string | null | undefined,
  currentUserId: string | undefined,
  targetUserId: string | undefined,
): boolean {
  return Boolean(
    currentRole === "super_admin" &&
      currentTitle === "president" &&
      currentUserId &&
      targetUserId &&
      currentUserId !== targetUserId,
  );
}
