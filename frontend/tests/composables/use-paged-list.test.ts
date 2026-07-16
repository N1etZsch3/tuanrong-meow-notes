import { describe, expect, it } from "vitest";

import { usePagedList, type PagedResponse } from "@/composables/use-paged-list";

interface Row {
  id: string;
}

function makePage(
  ids: string[],
  page: number,
  total: number,
  pageSize = 10,
): PagedResponse<Row> {
  return {
    items: ids.map((id) => ({ id })),
    page,
    page_size: pageSize,
    total,
    has_more: page * pageSize < total,
  };
}

describe("usePagedList", () => {
  it("loads the first page and reports totals", async () => {
    const list = usePagedList<Row>({
      pageSize: 10,
      getItemKey: (row) => row.id,
      fetchPage: async (page) => makePage(["a", "b"], page, 12),
    });

    await list.refresh();

    expect(list.items.value.map((row) => row.id)).toEqual(["a", "b"]);
    expect(list.total.value).toBe(12);
    expect(list.currentPage.value).toBe(1);
    expect(list.hasMore.value).toBe(true);
    expect(list.isLoading.value).toBe(false);
  });

  it("appends the next page and de-duplicates overlapping ids", async () => {
    let served = 0;
    const list = usePagedList<Row>({
      pageSize: 2,
      getItemKey: (row) => row.id,
      fetchPage: async (page) => {
        served += 1;
        return served === 1
          ? makePage(["a", "b"], page, 4, 2)
          : // 第二页故意包含一个重复 id "b"，验证去重
            makePage(["b", "c", "d"], page, 4, 2);
      },
    });

    await list.refresh();
    expect(list.hasMore.value).toBe(true);
    await list.loadMore();

    expect(list.items.value.map((row) => row.id)).toEqual(["a", "b", "c", "d"]);
    expect(list.currentPage.value).toBe(2);
    expect(list.hasMore.value).toBe(false);
  });

  it("does not load more when there is no next page", async () => {
    let calls = 0;
    const list = usePagedList<Row>({
      pageSize: 10,
      getItemKey: (row) => row.id,
      fetchPage: async (page) => {
        calls += 1;
        return makePage(["only"], page, 1);
      },
    });

    await list.refresh();
    await list.loadMore();

    expect(calls).toBe(1);
    expect(list.items.value.map((row) => row.id)).toEqual(["only"]);
  });

  it("captures errors on refresh and clears loading flags", async () => {
    const list = usePagedList<Row>({
      pageSize: 10,
      getItemKey: (row) => row.id,
      fallbackErrorMessage: "加载失败了",
      fetchPage: async () => {
        throw new Error("boom");
      },
    });

    await list.refresh();

    expect(list.errorMessage.value).toBe("boom");
    expect(list.isLoading.value).toBe(false);
    expect(list.items.value).toEqual([]);
  });
});
