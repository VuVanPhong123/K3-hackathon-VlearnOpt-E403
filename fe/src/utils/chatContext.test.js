import { describe, expect, it } from "vitest";

import { buildChatContext } from "./chatContext";

describe("buildChatContext", () => {
  it("uses dropped page attachment", () => {
    const context = buildChatContext({ activePage: 9, attachment: { type: "page", pageNumber: 5 } });
    expect(context.attached_pages).toEqual([5]);
    expect(context.active_page).toBe(9);
  });

  it("uses selected text attachment", () => {
    const context = buildChatContext({
      activePage: 1,
      attachment: { type: "text_selection", pageNumber: 2, selectedText: "RAG", boundingBoxes: [{ x: 0, y: 0, width: 0.4, height: 0.1 }] },
    });
    expect(context.text_selection.page_number).toBe(2);
    expect(context.text_selection.selected_text).toBe("RAG");
  });

  it("uses visual region attachment", () => {
    const bbox = { x: 0.1, y: 0.2, width: 0.3, height: 0.4 };
    const context = buildChatContext({ activePage: 1, attachment: { type: "visual_region", pageNumber: 6, bbox } });
    expect(context.visual_region).toEqual({ page_number: 6, bbox });
  });
});
