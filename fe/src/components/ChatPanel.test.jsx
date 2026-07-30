import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { PDF_PAGE_MIME } from "../constants/dragTypes";
import { deleteConversation, streamChatV2 } from "../services/api";
import ChatPanel from "./ChatPanel";

vi.mock("../services/api", () => ({
  deleteConversation: vi.fn(),
  streamChatV2: vi.fn(),
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

function mockStreamAnswer(answer = "Câu trả lời từ Tutor.") {
  streamChatV2.mockImplementation(async (payload, handlers) => {
    handlers.onMeta?.({ conversation_id: "conversation-1", trace_id: "trace-1", mode: "GENERAL_CHAT" });
    handlers.onDelta?.({ text: answer.slice(0, 4) });
    handlers.onDelta?.({ text: answer.slice(4) });
    handlers.onDone?.({
      answer,
      conversation_id: "conversation-1",
      provider: "openai",
      model: "fake",
      fallback_used: false,
      citations: [{ page_number: 2 }],
      trace: { provider: "openai", model: "fake", fallback: false },
    });
  });
}

describe("ChatPanel", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    deleteConversation.mockResolvedValue({ deleted: true });
    mockStreamAnswer();
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

  it("chat khi đang mở tài liệu gửi document_id và history fallback không chứa welcome", async () => {
    const user = userEvent.setup();
    render(<ChatPanel currentDocument={document} setContextAttachment={vi.fn()} />);

    await user.type(screen.getByLabelText("Câu hỏi cho Tutor"), "Tôi nên học thế nào?");
    await user.click(screen.getByRole("button", { name: "Gửi câu hỏi" }));

    await waitFor(() => expect(streamChatV2).toHaveBeenCalledTimes(1));
    expect(streamChatV2.mock.calls[0][0]).toMatchObject({
      document_id: "doc-1",
      context: { attached_pages: [] },
      answer_mode: "document_only",
      history: [],
    });
  });

  it("delta nối vào một assistant bubble và done gắn citation/provider/model", async () => {
    const user = userEvent.setup();
    render(<ChatPanel currentDocument={document} setContextAttachment={vi.fn()} />);

    await user.type(screen.getByLabelText("Câu hỏi cho Tutor"), "Giải thích giúp tôi.");
    await user.click(screen.getByRole("button", { name: "Gửi câu hỏi" }));

    expect(await screen.findByText("Câu trả lời từ Tutor.")).toBeInTheDocument();
    expect(screen.getByText("OpenAI")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Trang 2" })).toBeInTheDocument();
    expect(screen.getAllByText("Câu trả lời từ Tutor.")).toHaveLength(1);
  });

  it.each([
    {
      state: "cần làm rõ",
      response: {
        needs_clarification: true,
        abstained: false,
        trace: { decision: "clarify" },
      },
      status: "Cần thêm thông tin",
      decision: "Quyết định: Yêu cầu làm rõ",
    },
    {
      state: "từ chối suy đoán",
      response: {
        needs_clarification: false,
        abstained: true,
        trace: { decision: "abstain" },
      },
      status: "Chưa đủ bằng chứng",
      decision: "Quyết định: Không suy đoán",
    },
  ])("lưu và hiển thị trạng thái $state từ phản hồi", async ({ response, status, decision }) => {
    const user = userEvent.setup();
    streamChatV2.mockImplementationOnce(async (payload, handlers) => {
      handlers.onMeta?.({ conversation_id: "conversation-safe" });
      handlers.onDone?.({
        answer: "Phản hồi an toàn từ Tutor.",
        conversation_id: "conversation-safe",
        provider: "system",
        model: "conditional-gate-v1",
        fallback_used: false,
        citations: [],
        ...response,
      });
    });
    render(<ChatPanel currentDocument={document} setContextAttachment={vi.fn()} />);

    await user.type(screen.getByLabelText("Câu hỏi cho Tutor"), "Giải thích nội dung này.");
    await user.click(screen.getByRole("button", { name: "Gửi câu hỏi" }));

    expect(await screen.findByText(status)).toBeInTheDocument();
    expect(screen.getByText(decision)).toBeInTheDocument();
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

    await waitFor(() => expect(streamChatV2).toHaveBeenCalledTimes(1));
    expect(streamChatV2.mock.calls[0][0]).toMatchObject({
      document_id: "doc-1",
      context: { attached_pages: [3] },
      answer_mode: "document_only",
    });
  });

  it("nút tạo conversation mới reset UI và gọi DELETE conversation", async () => {
    const user = userEvent.setup();
    render(<ChatPanel currentDocument={document} setContextAttachment={vi.fn()} />);
    await user.type(screen.getByLabelText("Câu hỏi cho Tutor"), "Câu hỏi cũ");
    await user.click(screen.getByRole("button", { name: "Gửi câu hỏi" }));
    await screen.findByText("Câu trả lời từ Tutor.");

    await user.click(screen.getByRole("button", { name: "Tạo cuộc trò chuyện mới" }));

    await waitFor(() => expect(deleteConversation).toHaveBeenCalledWith("conversation-1"));
    expect(screen.queryByText("Câu hỏi cũ")).not.toBeInTheDocument();
    expect(screen.getAllByText(/Xin chào!/)).toHaveLength(1);
  });

  it("đổi tài liệu xóa conversation cũ và reset attachment/history", async () => {
    const user = userEvent.setup();
    const props = { setContextAttachment: vi.fn() };
    const { container, rerender } = render(
      <ChatPanel {...props} currentDocument={document} />,
    );
    fireEvent.drop(container.querySelector(".chat-panel"), {
      dataTransfer: dataTransfer(pagePayload(3)),
    });
    await user.type(screen.getByLabelText("Câu hỏi cho Tutor"), "Câu hỏi tài liệu cũ");
    await user.click(screen.getByRole("button", { name: "Gửi câu hỏi" }));
    await screen.findByText("Câu trả lời từ Tutor.");

    rerender(
      <ChatPanel
        {...props}
        currentDocument={{ id: "doc-2", original_filename: "mới.pdf" }}
      />,
    );

    await waitFor(() => expect(deleteConversation).toHaveBeenCalledWith("conversation-1"));
    expect(screen.queryByText("Câu hỏi tài liệu cũ")).not.toBeInTheDocument();
    expect(screen.queryByText("Trang 3")).not.toBeInTheDocument();
    expect(screen.getAllByText(/Xin chào!/)).toHaveLength(1);
  });

  it("error sau partial response giữ text đã nhận và hiện thử lại", async () => {
    const user = userEvent.setup();
    streamChatV2.mockImplementation(async (payload, handlers) => {
      handlers.onMeta?.({ conversation_id: "conversation-1" });
      handlers.onDelta?.({ text: "Một phần" });
      handlers.onError?.({ detail: "Mất kết nối", retryable: true });
    });
    render(<ChatPanel currentDocument={document} setContextAttachment={vi.fn()} />);

    await user.type(screen.getByLabelText("Câu hỏi cho Tutor"), "Câu hỏi lỗi");
    await user.click(screen.getByRole("button", { name: "Gửi câu hỏi" }));

    expect(await screen.findByText(/Một phần/)).toBeInTheDocument();
    expect(screen.getByText("Mất kết nối")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Thử lại" }));
    expect(screen.getByLabelText("Câu hỏi cho Tutor")).toHaveValue("Câu hỏi lỗi");
  });
});
