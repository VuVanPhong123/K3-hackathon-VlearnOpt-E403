import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import PdfPageCard from "../components/PdfPageCard";
import { usePageAnnotations } from "./usePageAnnotations";

vi.mock("react-pdf", () => ({
  Page: ({ pageNumber }) => <div>PDF {pageNumber}</div>,
}));

const horizontalStroke = {
  pageNumber: 1,
  tool: "pen",
  color: "#2563eb",
  width: 4,
  opacity: 0.92,
  points: [
    { x: 0.1, y: 0.5 },
    { x: 0.9, y: 0.5 },
  ],
};

function HookHarness({ documentId, tool = "pointer" }) {
  const annotations = usePageAnnotations(documentId);
  return (
    <div>
      <button onClick={() => annotations.addStroke(1, horizontalStroke)}>Thêm trang 1</button>
      <button onClick={() => annotations.addStroke(2, { ...horizontalStroke, pageNumber: 2 })}>Thêm trang 2</button>
      <button onClick={() => annotations.undoPage(1)}>Hoàn tác trang 1</button>
      <button onClick={() => annotations.clearPage(1)}>Xóa trang 1</button>
      <span data-testid="page-1-count">{annotations.getStrokes(1).length}</span>
      <span data-testid="page-2-count">{annotations.getStrokes(2).length}</span>
      <PdfPageCard
        document={{ id: documentId, original_filename: `${documentId}.pdf` }}
        pageNumber={1}
        width={720}
        tool={tool}
        color="#2563eb"
        strokeWidth={4}
        getStrokes={annotations.getStrokes}
        addStroke={annotations.addStroke}
        eraseNearPoint={annotations.eraseNearPoint}
      />
    </div>
  );
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

function eraseAt(overlay, x, y) {
  act(() => fireEvent.pointerDown(overlay, {
    pointerId: 1,
    isPrimary: true,
    button: 0,
    buttons: 1,
    clientX: x,
    clientY: y,
  }));
}

describe("usePageAnnotations với PdfPageCard", () => {
  beforeEach(() => localStorage.clear());

  it("eraser xóa giữa segment nhưng không xóa stroke ở xa", async () => {
    const { container } = render(<HookHarness documentId="doc-a" tool="eraser" />);
    fireEvent.click(screen.getByText("Thêm trang 1"));
    expect(screen.getByTestId("page-1-count")).toHaveTextContent("1");

    eraseAt(prepareOverlay(container), 50, 10);
    expect(screen.getByTestId("page-1-count")).toHaveTextContent("1");

    eraseAt(prepareOverlay(container), 50, 50);
    expect(screen.getByTestId("page-1-count")).toHaveTextContent("0");
  });

  it("undo và clear chỉ ảnh hưởng trang hiện tại", () => {
    render(<HookHarness documentId="doc-a" />);
    fireEvent.click(screen.getByText("Thêm trang 1"));
    fireEvent.click(screen.getByText("Thêm trang 1"));
    fireEvent.click(screen.getByText("Thêm trang 2"));

    fireEvent.click(screen.getByText("Hoàn tác trang 1"));
    expect(screen.getByTestId("page-1-count")).toHaveTextContent("1");
    expect(screen.getByTestId("page-2-count")).toHaveTextContent("1");

    fireEvent.click(screen.getByText("Xóa trang 1"));
    expect(screen.getByTestId("page-1-count")).toHaveTextContent("0");
    expect(screen.getByTestId("page-2-count")).toHaveTextContent("1");
  });

  it("tách annotation theo document và khôi phục từ localStorage", async () => {
    const first = render(<HookHarness documentId="doc-a" />);
    fireEvent.click(screen.getByText("Thêm trang 1"));
    await waitFor(() =>
      expect(JSON.parse(localStorage.getItem("vlearn-annotations:doc-a"))["1"]).toHaveLength(1),
    );
    first.unmount();

    const second = render(<HookHarness documentId="doc-b" />);
    expect(screen.getByTestId("page-1-count")).toHaveTextContent("0");
    second.unmount();

    render(<HookHarness documentId="doc-a" />);
    await waitFor(() =>
      expect(screen.getByTestId("page-1-count")).toHaveTextContent("1"),
    );
  });
});
