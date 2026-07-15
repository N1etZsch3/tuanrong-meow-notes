interface PageStackItem {
  route?: string;
}

function normalizeRoute(route: string): string {
  return route.replace(/^\/+/, "");
}

export function returnToListAfterDelete(listRoute: string): void {
  const targetRoute = normalizeRoute(listRoute);
  const pages = getCurrentPages() as PageStackItem[];

  for (let index = pages.length - 2; index >= 0; index -= 1) {
    if (normalizeRoute(pages[index]?.route || "") !== targetRoute) {
      continue;
    }

    uni.navigateBack({ delta: pages.length - 1 - index });
    return;
  }

  uni.reLaunch({ url: `/${targetRoute}` });
}
