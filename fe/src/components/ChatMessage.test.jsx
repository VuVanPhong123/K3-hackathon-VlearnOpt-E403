import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import ChatMessage from "./ChatMessage";

describe("ChatMessage", () => {
  it("đi tới đúng trang khi bấm citation", () => {
    const onCitationClick = vi.fn();
    render(
      <ChatMessage
        message={{
          role: "assistant",
          content: "Câu trả lời",
          citations: [{ page_number: 4 }],
          provider: "openai",
        }}
        onCitationClick={onCitationClick}
      />,
    );
    fireEvent.click(screen.getByText("Trang 4"));
    expect(onCitationClick).toHaveBeenCalledWith(4);
    expect(screen.getByText("OpenAI")).toBeInTheDocument();
  });

  it("hiển thị Gemini dự phòng bằng tiếng Việt", () => {
    render(
      <ChatMessage
        message={{
          role: "assistant",
          content: "Câu trả lời",
          provider: "gemini",
          fallbackUsed: true,
        }}
      />,
    );
    expect(screen.getByText("Gemini dự phòng")).toBeInTheDocument();
  });
});
