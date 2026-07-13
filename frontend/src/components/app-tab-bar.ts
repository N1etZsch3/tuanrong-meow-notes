import mapIcon from "../../素材/svg/默认/地图.svg";
import messagesIcon from "../../素材/svg/默认/喵息.svg";
import profileIcon from "../../素材/svg/默认/我的.svg";
import tasksIcon from "../../素材/svg/默认/任务.svg";

export type AppTabKey = "map" | "messages" | "tasks" | "profile";

export interface AppTabItem {
  key: AppTabKey;
  label: string;
  route: string;
  icon: string;
  preserveActiveIconColor?: boolean;
}

export const APP_TAB_ITEMS: readonly AppTabItem[] = [
  {
    key: "map",
    label: "喵图",
    route: "/pages/index/index",
    icon: mapIcon,
    preserveActiveIconColor: true,
  },
  {
    key: "messages",
    label: "喵息",
    route: "/pages/messages/index",
    icon: messagesIcon,
  },
  {
    key: "tasks",
    label: "喵记",
    route: "/pages/tasks/index",
    icon: tasksIcon,
  },
  {
    key: "profile",
    label: "喵的",
    route: "/pages/profile/index",
    icon: profileIcon,
  },
] as const;

const DEFAULT_TAB_KEY: AppTabKey = "map";

function normalizeRoutePath(route: string): string {
  const path = route.split(/[?#]/)[0] ?? "";
  if (!path) {
    return "";
  }

  return path.startsWith("/") ? path : `/${path}`;
}

export function getActiveTabKey(route: string): AppTabKey {
  const normalizedRoute = normalizeRoutePath(route);
  const matchedItem = APP_TAB_ITEMS.find(
    (item) => item.route === normalizedRoute,
  );

  return matchedItem?.key ?? DEFAULT_TAB_KEY;
}

export function getTabTarget(tabKey: AppTabKey): string {
  return (
    APP_TAB_ITEMS.find((item) => item.key === tabKey)?.route ??
    APP_TAB_ITEMS[0].route
  );
}

export function shouldNavigateTab(
  tabKey: AppTabKey,
  currentRoute: string,
): boolean {
  return getTabTarget(tabKey) !== normalizeRoutePath(currentRoute);
}
