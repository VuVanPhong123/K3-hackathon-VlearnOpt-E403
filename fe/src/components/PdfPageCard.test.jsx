import { act, fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { PDF_PAGE_MIME } from "../constants/dragTypes";
import PdfPageCard from "./PdfPageCard";

vi.mock("react-pdf", () => ({
  Page: ({ pageNumber, onRenderSuccess }) => (
    <button className="textLayer" type="button" data-testid={`pdf-page-${pageNumber}`} onClick={onRenderSuccess}>
      PDF {pageNumber}
    </button>
  ),
}));

const document = {
  id: "doc-1",
  original_filename: "bài-học.pdf",
};

function baseProps(overrides = {}) {
  return {
    document,
    pageNumber: 3,
    width: 720,
    tool: "pointer",
    color: "#2563eb",
    strokeWidth: 4,
    getStrokes: () => [],
    addStroke: vi.fn(),
    eraseNearPoint: vi.fn(),
    onAttachPage: vi.fn(),
    ...overrides,
  };
}

function prepareOverlay(container) {
  const overlay = container.querySelector("svg.annotation-layer");
  overlay.getBoundingClientRect = () => ({
    left: 0,
    top: 0,
    width: 100,
    height: 100,
    right: 100,
    bottom: 100,
  });
  overlay.setPointerCapture = vi.fn();
  overlay.releasePointerCapture = vi.fn();
  overlay.hasPointerCapture = vi.fn(() => false);
  return overlay;
}

function pointer(target, type, options) {
  const properties = {
    pointerId: 1,
    isPrimary: true,
    button: 0,
    buttons: 1,
    clientX: 10,
    clientY: 10,
    ...options,
  };
  const dispatch = {
    pointerdown: fireEvent.pointerDown,
    pointermove: fireEvent.pointerMove,
    pointerup: fireEvent.pointerUp,
  }[type];
  act(() => dispatch(target, properties));
}

describe("PdfPageCard", () => {
  it("drag trang 3 tạo đủ payload kể cả khi tool là pen", () => {
    const props = baseProps({ tool: "pen" });
    const { container } = render(<PdfPageCard {...props} />);
    const values = {};
    const transfer = {
      setData: vi.fn((type, value) => {
        values[type] = value;
      }),
      effectAllowed: "none",
    };

    fireEvent.dragStart(
      screen.getByRole("button", { name: "Kéo trang 3 vào Tutor" }),
      { dataTransfer: transfer },
    );

    expect(JSON.parse(values[PDF_PAGE_MIME])).toEqual({
      type: "page",
      documentId: "doc-1",
      pageNumber: 3,
      filename: "bài-học.pdf",
    });
    expect(values["text/plain"]).toBe(values[PDF_PAGE_MIME]);
    expect(transfer.effectAllowed).toBe("copy");
    expect(container.querySelector(".page-card")).toHaveClass("dragging");
  });

  it("nút fallback gắn đúng trang mà không tự gửi câu hỏi", () => {
    const onAttachPage = vi.fn();
    render(<PdfPageCard {...baseProps({ onAttachPage })} />);
    fireEvent.click(screen.getByRole("button", { name: "Gắn trang 3 vào chat" }));
    expect(onAttachPage).toHaveBeenCalledWith({
      type: "page",
      documentId: "doc-1",
      pageNumber: 3,
      filename: "bài-học.pdf",
    });
  });

  it("pen hiển thị draft và lưu stroke sau pointerup", () => {
    const addStroke = vi.fn();
    const { container } = render(
      <PdfPageCard {...baseProps({ tool: "pen", addStroke })} />,
    );
    const overlay = prepareOverlay(container);

    pointer(overlay, "pointerdown", { clientX: 10, clientY: 10 });
    pointer(overlay, "pointermove", { clientX: 60, clientY: 60 });
    expect(container.querySelector("svg.annotation-layer path")).toBeInTheDocument();
    expect(container.querySelector("svg.annotation-layer path").getAttribute("d")).toContain("L");
    pointer(overlay, "pointerup", { clientX: 60, clientY: 60, buttons: 0 });

    expect(addStroke).toHaveBeenCalledTimes(1);
    expect(addStroke.mock.calls[0][1]).toMatchObject({
      tool: "pen",
      color: "#2563eb",
      width: 4,
      opacity: 0.92,
    });
  });

  it("highlighter dùng nét dày và opacity thấp", () => {
    const addStroke = vi.fn();
    const { container } = render(
      <PdfPageCard {...baseProps({ tool: "highlighter", addStroke })} />,
    );
    const overlay = prepareOverlay(container);

    pointer(overlay, "pointerdown", { clientX: 10, clientY: 10 });
    pointer(overlay, "pointermove", { clientX: 70, clientY: 20 });
    pointer(overlay, "pointerup", { clientX: 70, clientY: 20, buttons: 0 });

    expect(addStroke.mock.calls[0][1].width).toBeGreaterThanOrEqual(12);
    expect(addStroke.mock.calls[0][1].opacity).toBe(0.28);
  });

  it.each(["pen", "highlighter", "eraser"])("%s không tạo chat attachment", (tool) => {
    const onAttachPage = vi.fn();
    const { container } = render(
      <PdfPageCard {...baseProps({ tool, onAttachPage })} />,
    );
    const overlay = prepareOverlay(container);
    pointer(overlay, "pointerdown", { clientX: 10, clientY: 10 });
    pointer(overlay, "pointermove", { clientX: 40, clientY: 40 });
    pointer(overlay, "pointerup", { clientX: 40, clientY: 40, buttons: 0 });
    expect(onAttachPage).not.toHaveBeenCalled();
  });

  it("bôi đen văn bản thật hiện popup và tạo selection attachment", () => {
    const onAttachPage = vi.fn();
    const { container } = render(
      <PdfPageCard {...baseProps({ onAttachPage })} />,
    );
    const shell = container.querySelector(".page-shell");
    const textLayer = screen.getByTestId("pdf-page-3");
    const textNode = textLayer.firstChild;
    shell.getBoundingClientRect = () => ({
      left: 0,
      top: 0,
      width: 720,
      height: 900,
      right: 720,
      bottom: 900,
    });
    const range = {
      getClientRects: () => [
        { left: 72, top: 90, width: 180, height: 20, right: 252, bottom: 110 },
      ],
      getBoundingClientRect: () => ({
        left: 72,
        top: 90,
        width: 180,
        height: 20,
        right: 252,
        bottom: 110,
      }),
    };
    vi.spyOn(window, "getSelection").mockReturnValue({
      isCollapsed: false,
      anchorNode: textNode,
      focusNode: textNode,
      toString: () => "PDF 3",
      getRangeAt: () => range,
      removeAllRanges: vi.fn(),
    });

    fireEvent.mouseUp(textLayer);
    fireEvent.click(screen.getByRole("button", { name: "Hỏi AI" }));

    expect(onAttachPage).toHaveBeenCalledWith(
      expect.objectContaining({
        type: "text_selection",
        documentId: "doc-1",
        pageNumber: 3,
        selectedText: "PDF 3",
        boundingBoxes: [
          expect.objectContaining({ x: 0.1, y: 0.1, width: 0.25 }),
        ],
      }),
    );
  });

  it("tool khoanh vùng tạo bbox normalized và chỉ attach khi bấm Hỏi AI", () => {
    const onAttachPage = vi.fn();
    const setTool = vi.fn();
    const { container } = render(
      <PdfPageCard
        {...baseProps({ tool: "ask_region", onAttachPage, setTool })}
      />,
    );
    const shell = container.querySelector(".page-shell");
    shell.getBoundingClientRect = () => ({
      left: 0,
      top: 0,
      width: 100,
      height: 100,
      right: 100,
      bottom: 100,
    });
    const layer = container.querySelector(".region-select-layer");
    pointer(layer, "pointerdown", { clientX: 10, clientY: 20 });
    pointer(layer, "pointermove", { clientX: 60, clientY: 70 });
    pointer(layer, "pointerup", { clientX: 60, clientY: 70, buttons: 0 });
    expect(onAttachPage).not.toHaveBeenCalled();

    fireEvent.click(screen.getByRole("button", { name: "Hỏi AI" }));
    expect(onAttachPage).toHaveBeenCalledWith(
      expect.objectContaining({
        type: "visual_region",
        documentId: "doc-1",
        pageNumber: 3,
        filename: "bài-học.pdf",
        bbox: expect.objectContaining({
          x: expect.closeTo(0.1),
          y: expect.closeTo(0.2),
          width: expect.closeTo(0.5),
          height: expect.closeTo(0.5),
        }),
      }),
    );
    expect(setTool).toHaveBeenCalledWith("pointer");
  });

  it("giữ nguyên tọa độ normalized ở zoom 70%, 100% và 150%", () => {
    const stroke = {
      pageNumber: 3,
      tool: "pen",
      color: "#2563eb",
      width: 4,
      opacity: 0.92,
      points: [
        { x: 0.1, y: 0.2 },
        { x: 0.8, y: 0.7 },
      ],
    };
    const props = baseProps({ getStrokes: () => [stroke] });
    const { container, rerender } = render(
      <PdfPageCard {...props} width={504} />,
    );
    const pathAt70 = container.querySelector("svg.annotation-layer path").getAttribute("d");
    expect(container.querySelector(".page-shell")).toHaveStyle({ width: "504px" });

    rerender(<PdfPageCard {...props} width={720} />);
    expect(container.querySelector("svg.annotation-layer path")).toHaveAttribute("d", pathAt70);
    expect(container.querySelector(".page-shell")).toHaveStyle({ width: "720px" });

    rerender(<PdfPageCard {...props} width={1080} />);
    expect(container.querySelector("svg.annotation-layer path")).toHaveAttribute("d", pathAt70);
    expect(container.querySelector(".page-shell")).toHaveStyle({ width: "1080px" });
  });
});
