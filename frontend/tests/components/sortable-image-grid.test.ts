import { describe, expect, it } from "vitest";

import sortableImageGridSource from "../../src/components/SortableImageGrid.vue?raw";
import { moveArrayItem } from "@/utils/array-order";

describe("sortable image grid", () => {
  it("moves an image to the target position without mutating the source", () => {
    const source = ["first", "second", "third"];

    expect(moveArrayItem(source, 2, 0)).toEqual(["third", "first", "second"]);
    expect(source).toEqual(["first", "second", "third"]);
  });

  it("supports long-press drag ordering and identifies the first image as cover", () => {
    expect(sortableImageGridSource).toContain('@longpress="beginDrag(index)"');
    expect(sortableImageGridSource).toContain('@touchmove.stop.prevent="handleDragMove"');
    expect(sortableImageGridSource).toContain('emit("reorder"');
    expect(sortableImageGridSource).toContain("第一张将作为封面");
    expect(sortableImageGridSource).toContain('class="sortable-image-cover"');
  });
});
