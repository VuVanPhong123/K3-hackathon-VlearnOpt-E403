import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import ChatMessage from "./ChatMessage";

describe("ChatMessage", () => {
  it("calls citation click with the page number", () => {
    const onCitationClick = vi.fn();
    render(
      <ChatMessage
        message={{ role: "assistant", content: "Answer", citations: [{ page_number: 4 }], provider: "deterministic", confidence: 0.8 }}
        onCitationClick={onCitationClick}
      />,
    );
    fireEvent.click(screen.getByText("page 4"));
    expect(onCitationClick).toHaveBeenCalledWith(4);
  });

  it("shows low confidence state", () => {
    render(<ChatMessage message={{ role: "assistant", content: "Answer", confidence: 0.2 }} />);
    expect(screen.getByText(/Not enough grounding/)).toBeInTheDocument();
  });
});
