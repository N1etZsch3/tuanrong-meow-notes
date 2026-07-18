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
  currentTitle: string | null | undefined,
  currentUserId: string | undefined,
  targetUserId: string | undefined,
): boolean {
  return Boolean(
    currentTitle === "president" &&
      currentUserId &&
      targetUserId &&
      currentUserId !== targetUserId,
  );
}
