import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { PDF_PAGE_MIME } from "../constants/dragTypes";
import { sendChatV2 } from "../services/api";
import ChatPanel from "./ChatPanel";

vi.mock("../services/api", () => ({
  sendChatV2: vi.fn(),
}));

function dataTransfer(payload, mime = PDF_PAGE_MIME) {
  const values = {
    [mime]: typeof payload === "string" ? payload : JSON.stringify(payload),
  };
  return {
    getData: vi.fn((type) => values[type] || ""),
    setData: vi.fn((type, value) => {
      values[type] = value;
    }),
    dropEffect: "none",
    effectAllowed: "none",
  };
}

const document = {
  id: "doc-1",
  original_filename: "bài-học.pdf",
};

function pagePayload(pageNumber, documentId = "doc-1") {
  return {
    type: "page",
    documentId,
    pageNumber,
    filename: "bài-học.pdf",
  };
}

describe("ChatPanel", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    sendChatV2.mockResolvedValue({
      answer: "Câu trả lời từ Tutor.",
      conversation_id: "conversation-1",
      provider: "openai",
      model: "fake",
      fallback_used: false,
      citations: [],
    });
  });

  it("hiển thị giao diện tiếng Việt và không còn tính năng ngoài scope", () => {
    render(<ChatPanel currentDocument={document} setContextAttachment={vi.fn()} />);

    expect(screen.getByText(/Xin chào!/)).toBeInTheDocument();
    expect(screen.getByText("Trợ lý học tập theo ngữ cảnh")).toBeInTheDocument();
    expect(screen.queryByText("Summary")).not.toBeInTheDocument();
    expect(screen.queryByText("Quiz")).not.toBeInTheDocument();
    expect(screen.queryByText("Selection")).not.toBeInTheDocument();
    expect(screen.queryByRole("checkbox")).not.toBeInTheDocument();
  });

  it("chat khi đang mở tài liệu gửi document_id để backend tự định tuyến", async () => {
    const user = userEvent.setup();
    render(<ChatPanel currentDocument={document} setContextAttachment={vi.fn()} />);

    await user.type(screen.getByLabelText("Câu hỏi cho Tutor"), "Tôi nên học thế nào?");
    await user.click(screen.getByRole("button", { name: "Gửi câu hỏi" }));

    await waitFor(() => expect(sendChatV2).toHaveBeenCalledTimes(1));
    expect(sendChatV2.mock.calls[0][0]).toMatchObject({
      document_id: "doc-1",
      context: { attached_pages: [] },
      answer_mode: "document_only",
    });
  });

  it("drop trang tạo attachment, trang mới thay trang cũ và remove hoạt động", () => {
    const setContextAttachment = vi.fn();
    const { container } = render(
      <ChatPanel currentDocument={document} setContextAttachment={setContextAttachment} />,
    );
    const panel = container.querySelector(".chat-panel");

    fireEvent.drop(panel, { dataTransfer: dataTransfer(pagePayload(3)) });
    expect(screen.getByText("Trang 3")).toBeInTheDocument();
    expect(setContextAttachment).toHaveBeenLastCalledWith(pagePayload(3));

    fireEvent.drop(panel, { dataTransfer: dataTransfer(pagePayload(5)) });
    expect(screen.queryByText("Trang 3")).not.toBeInTheDocument();
    expect(screen.getByText("Trang 5")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Gỡ ngữ cảnh đã gắn" }));
    expect(screen.queryByText("Trang 5")).not.toBeInTheDocument();
    expect(setContextAttachment).toHaveBeenLastCalledWith(null);
  });

  it("từ chối payload sai và trang của tài liệu khác", () => {
    const { container } = render(
      <ChatPanel currentDocument={document} setContextAttachment={vi.fn()} />,
    );
    const panel = container.querySelector(".chat-panel");

    fireEvent.drop(panel, {
      dataTransfer: dataTransfer({ type: "page", documentId: "doc-1", pageNumber: 0, filename: "" }),
    });
    expect(screen.getByText("Dữ liệu trang PDF không hợp lệ.")).toBeInTheDocument();

    fireEvent.drop(panel, {
      dataTransfer: dataTransfer(pagePayload(3, "doc-2")),
    });
    expect(screen.getByText("Trang này không thuộc tài liệu đang mở.")).toBeInTheDocument();
    expect(screen.queryByText("Trang 3")).not.toBeInTheDocument();
  });

  it("page chat gửi đúng document và page", async () => {
    const user = userEvent.setup();
    const { container } = render(
      <ChatPanel currentDocument={document} setContextAttachment={vi.fn()} />,
    );
    fireEvent.drop(container.querySelector(".chat-panel"), {
      dataTransfer: dataTransfer(pagePayload(3)),
    });

    await user.type(screen.getByLabelText("Câu hỏi cho Tutor"), "Giải thích trang này.");
    await user.click(screen.getByRole("button", { name: "Gửi câu hỏi" }));

    await waitFor(() => expect(sendChatV2).toHaveBeenCalledTimes(1));
    expect(sendChatV2.mock.calls[0][0]).toMatchObject({
      document_id: "doc-1",
      context: { attached_pages: [3] },
      answer_mode: "document_only",
    });
  });

  it("đổi tài liệu reset attachment, hội thoại và lời nhắn", async () => {
    const user = userEvent.setup();
    const props = { setContextAttachment: vi.fn() };
    const { rerender } = render(
      <ChatPanel {...props} currentDocument={document} />,
    );
    await user.type(screen.getByLabelText("Câu hỏi cho Tutor"), "Câu hỏi tài liệu cũ");
    await user.click(screen.getByRole("button", { name: "Gửi câu hỏi" }));
    await screen.findByText("Câu trả lời từ Tutor.");

    rerender(
      <ChatPanel
        {...props}
        currentDocument={{ id: "doc-2", original_filename: "mới.pdf" }}
      />,
    );

    expect(screen.queryByText("Câu hỏi tài liệu cũ")).not.toBeInTheDocument();
    expect(screen.getAllByText(/Xin chào!/)).toHaveLength(1);
  });
});
