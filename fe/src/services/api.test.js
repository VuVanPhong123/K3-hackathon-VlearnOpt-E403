import { beforeEach, describe, expect, it, vi } from "vitest";

import { parseSseBlock, streamChatV2 } from "./api";

function responseFromChunks(chunks) {
  const encoder = new TextEncoder();
  return {
    ok: true,
    body: new ReadableStream({
      start(controller) {
        for (const chunk of chunks) {
          controller.enqueue(encoder.encode(chunk));
        }
        controller.close();
      },
    }),
    headers: new Headers({ "content-type": "text/event-stream" }),
  };
}

describe("SSE chat API", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("parseSseBlock đọc event JSON", () => {
    expect(parseSseBlock('event: delta\ndata: {"text":"Xin chào"}')).toEqual({
      event: "delta",
      data: { text: "Xin chào" },
    });
  });

  it("streamChatV2 parse event bị chia network chunk", async () => {
    const onDelta = vi.fn();
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      responseFromChunks(['event: delta\ndata: {"text":"Xin', ' chào"}\n\n']),
    );

    await streamChatV2({ message: "hi" }, { onDelta });

    expect(onDelta).toHaveBeenCalledWith({ text: "Xin chào" });
  });

  it("streamChatV2 parse nhiều event trong một chunk", async () => {
    const onMeta = vi.fn();
    const onDone = vi.fn();
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      responseFromChunks([
        'event: meta\ndata: {"conversation_id":"c1"}\n\n' +
          'event: done\ndata: {"answer":"x","citations":[]}\n\n',
      ]),
    );

    await streamChatV2({ message: "hi" }, { onMeta, onDone });

    expect(onMeta).toHaveBeenCalledWith({ conversation_id: "c1" });
    expect(onDone).toHaveBeenCalledWith({ answer: "x", citations: [] });
  });

  it("streamChatV2 giữ đúng UTF-8 multibyte", async () => {
    const onDelta = vi.fn();
    const encoder = new TextEncoder();
    const bytes = encoder.encode('event: delta\ndata: {"text":"Tiếng Việt"}\n\n');
    vi.spyOn(globalThis, "fetch").mockResolvedValue({
      ok: true,
      body: new ReadableStream({
        start(controller) {
          controller.enqueue(bytes.slice(0, 31));
          controller.enqueue(bytes.slice(31));
          controller.close();
        },
      }),
      headers: new Headers({ "content-type": "text/event-stream" }),
    });

    await streamChatV2({ message: "hi" }, { onDelta });

    expect(onDelta).toHaveBeenCalledWith({ text: "Tiếng Việt" });
  });
});
