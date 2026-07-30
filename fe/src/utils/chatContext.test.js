import { describe, expect, it } from "vitest";

import { buildChatContext } from "./chatContext";

describe("buildChatContext", () => {
  it("chỉ gửi đúng trang PDF đã gắn", () => {
    expect(
      buildChatContext({
        attachment: { type: "page", pageNumber: 5 },
        activePage: 9,
      }),
    ).toEqual({
      attached_pages: [5],
      active_page: 9,
      text_selection: null,
      visual_region: null,
    });
  });

  it("gửi vùng hình ảnh theo bbox chuẩn hóa", () => {
    const bbox = { x: 0.1, y: 0.2, width: 0.4, height: 0.3 };
    expect(
      buildChatContext({
        attachment: { type: "visual_region", pageNumber: 6, bbox },
      }),
    ).toEqual({
      attached_pages: [],
      active_page: null,
      text_selection: null,
      visual_region: { page_number: 6, bbox },
    });
  });

  it("gửi đoạn văn bản và các hộp giới hạn", () => {
    const boundingBoxes = [{ x: 0.1, y: 0.2, width: 0.3, height: 0.04 }];
    expect(
      buildChatContext({
        attachment: {
          type: "text_selection",
          pageNumber: 2,
          selectedText: "Nội dung được chọn",
          boundingBoxes,
        },
      }),
    ).toMatchObject({
      text_selection: {
        page_number: 2,
        selected_text: "Nội dung được chọn",
        bounding_boxes: boundingBoxes,
      },
    });
  });
});
