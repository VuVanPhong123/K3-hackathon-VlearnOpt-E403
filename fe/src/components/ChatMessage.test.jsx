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

  it("render Markdown, code, bảng và công thức", () => {
    const { container } = render(
      <ChatMessage
        message={{
          role: "assistant",
          content:
            "## Ý chính\n\n- Mục **quan trọng**\n\n`inline`\n\n```js\nconst x = 1;\n```\n\n| A | B |\n|---|---|\n| 1 | 2 |\n\n$$x^2 + y^2$$",
        }}
      />,
    );

    expect(screen.getByRole("heading", { name: "Ý chính" })).toBeInTheDocument();
    expect(screen.getByText("quan trọng")).toBeInTheDocument();
    expect(container.querySelector(".code-block")).toHaveTextContent("const x = 1;");
    expect(screen.getByRole("table")).toBeInTheDocument();
    expect(container.querySelector(".katex")).toBeInTheDocument();
  });
});
