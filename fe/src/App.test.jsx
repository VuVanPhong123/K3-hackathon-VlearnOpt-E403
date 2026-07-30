import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import App from "./App";

vi.mock("./components/PdfWorkspace", () => ({
  default: () => <div>Không gian PDF</div>,
}));

vi.mock("./components/ChatPanel", () => ({
  default: () => <div>Khung chat</div>,
}));

vi.mock("./services/api", () => ({
  healthCheck: vi.fn(() => Promise.resolve({ status: "ok" })),
  listDocuments: vi.fn(() => Promise.resolve([])),
  getDocumentStatus: vi.fn(),
  uploadDocument: vi.fn(),
}));

describe("divider hai panel", () => {
  beforeEach(() => {
    localStorage.clear();
    Object.defineProperty(window, "innerWidth", {
      configurable: true,
      value: 1200,
    });
  });

  it("resize bằng pointer và lưu độ rộng", async () => {
    render(<App />);
    const divider = screen.getByRole("separator", {
      name: "Thay đổi độ rộng khung chat",
    });
    const initial = Number(divider.getAttribute("aria-valuenow"));

    fireEvent.pointerDown(divider, { button: 0, clientX: 700 });
    fireEvent.pointerMove(window, { clientX: 650 });
    fireEvent.pointerUp(window);

    await waitFor(() =>
      expect(Number(divider.getAttribute("aria-valuenow"))).toBe(initial + 50),
    );
    expect(localStorage.getItem("vlearn-chat-panel-width")).toBe(
      String(initial + 50),
    );
    expect(document.body).not.toHaveClass("resizing-panels");
  });

  it("khôi phục width và hỗ trợ bàn phím", async () => {
    localStorage.setItem("vlearn-chat-panel-width", "450");
    render(<App />);
    await act(async () => {
      await Promise.resolve();
    });
    const divider = screen.getByRole("separator");

    expect(divider).toHaveAttribute("aria-valuenow", "450");
    fireEvent.keyDown(divider, { key: "ArrowLeft" });
    expect(divider).toHaveAttribute("aria-valuenow", "466");
    fireEvent.keyDown(divider, { key: "ArrowRight", shiftKey: true });
    expect(divider).toHaveAttribute("aria-valuenow", "418");
  });
});
