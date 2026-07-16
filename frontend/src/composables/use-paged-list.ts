import { ref } from "vue";
import type { Ref } from "vue";

/**
 * 通用分页懒加载 composable（微信小程序原生 scroll-view @scrolltolower 方案）。
 *
 * 后端统一分页契约：请求 page/page_size，响应 { items, page, page_size, total, has_more }。
 * 页面把「取某一页」的函数传进来，composable 负责维护 reset/追加/去重/加载态/错误态，
 * 供 <scroll-view @scrolltolower="loadMore"> 直接调用。
 *
 * 参考现有 pages/cats/index.vue 已验证的懒加载实现，抽为共享逻辑避免每页复制。
 */
export interface PagedResponse<TItem> {
  items: TItem[];
  page: number;
  page_size: number;
  total: number;
  has_more: boolean;
}

export interface UsePagedListOptions<TItem> {
  /** 每页条数（本项目统一 10 条）。 */
  pageSize?: number;
  /** 取第 page 页数据。 */
  fetchPage: (page: number, pageSize: number) => Promise<PagedResponse<TItem>>;
  /** 项唯一键，用于追加时去重（分页边界重复防护）。 */
  getItemKey: (item: TItem) => string;
  /** 加载失败时的兜底错误文案。 */
  fallbackErrorMessage?: string;
}

export function usePagedList<TItem>(options: UsePagedListOptions<TItem>) {
  const pageSize = options.pageSize ?? 10;
  const fallbackError = options.fallbackErrorMessage ?? "加载失败，请稍后重试";

  const items = ref([]) as Ref<TItem[]>;
  const total = ref(0);
  const currentPage = ref(0);
  const hasMore = ref(false);
  const isLoading = ref(false);
  const isLoadingMore = ref(false);
  const errorMessage = ref("");

  async function load(reset: boolean): Promise<void> {
    if (reset) {
      if (isLoading.value) {
        return;
      }
      isLoading.value = true;
      errorMessage.value = "";
    } else {
      if (isLoading.value || isLoadingMore.value || !hasMore.value) {
        return;
      }
      isLoadingMore.value = true;
    }

    const nextPage = reset ? 1 : currentPage.value + 1;
    try {
      const response = await options.fetchPage(nextPage, pageSize);
      if (reset) {
        items.value = response.items;
      } else {
        const existingKeys = new Set(items.value.map(options.getItemKey));
        items.value = [
          ...items.value,
          ...response.items.filter((item) => !existingKeys.has(options.getItemKey(item))),
        ];
      }
      currentPage.value = response.page;
      total.value = response.total;
      hasMore.value = response.has_more;
    } catch (error) {
      if (reset) {
        errorMessage.value = error instanceof Error ? error.message : fallbackError;
      }
    } finally {
      isLoading.value = false;
      isLoadingMore.value = false;
    }
  }

  function refresh(): Promise<void> {
    return load(true);
  }

  function loadMore(): Promise<void> {
    return load(false);
  }

  function reset(): void {
    items.value = [];
    total.value = 0;
    currentPage.value = 0;
    hasMore.value = false;
    errorMessage.value = "";
  }

  return {
    items,
    total,
    currentPage,
    hasMore,
    isLoading,
    isLoadingMore,
    errorMessage,
    refresh,
    loadMore,
    reset,
  };
}
