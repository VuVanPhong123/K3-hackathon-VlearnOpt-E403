const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

async function parseResponse(response) {
  const contentType = response.headers.get("content-type") || "";
  const body = contentType.includes("application/json") ? await response.json() : await response.text();
  if (!response.ok) {
    const message = typeof body === "object" && body?.detail ? body.detail : "Không thể kết nối tới máy chủ.";
    throw new Error(message);
  }
  return body;
}

export async function healthCheck() {
  const response = await fetch(`${API_BASE_URL}/api/health`);
  return parseResponse(response);
}

export async function uploadDocument(file) {
  const formData = new FormData();
  formData.append("file", file);
  const response = await fetch(`${API_BASE_URL}/api/documents`, {
    method: "POST",
    body: formData,
  });
  return parseResponse(response);
}

export async function listDocuments() {
  const response = await fetch(`${API_BASE_URL}/api/documents`);
  return parseResponse(response);
}

export function getDocumentFileUrl(documentId) {
  return `${API_BASE_URL}/api/documents/${documentId}/file`;
}

export async function deleteDocument(documentId) {
  const response = await fetch(`${API_BASE_URL}/api/documents/${documentId}`, {
    method: "DELETE",
  });
  return parseResponse(response);
}

export async function deleteConversation(conversationId) {
  const response = await fetch(`${API_BASE_URL}/api/conversations/${conversationId}`, {
    method: "DELETE",
  });
  if (response.status === 404) {
    return { deleted: true, document_id: conversationId };
  }
  return parseResponse(response);
}

export function parseSseBlock(block) {
  const event = { event: "message", data: "" };
  for (const line of block.split(/\r?\n/)) {
    if (line.startsWith("event:")) {
      event.event = line.slice(6).trim();
    } else if (line.startsWith("data:")) {
      event.data += line.slice(5).trimStart();
    }
  }
  if (!event.data) return null;
  return {
    event: event.event,
    data: JSON.parse(event.data),
  };
}

export async function streamChatV2(payload, handlers = {}, signal) {
  const response = await fetch(`${API_BASE_URL}/api/v2/chat/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
    signal,
  });
  if (!response.ok || !response.body) {
    await parseResponse(response);
    return;
  }

  const decoder = new TextDecoder("utf-8");
  const reader = response.body.getReader();
  let buffer = "";

  async function flushBlock(block) {
    const parsed = parseSseBlock(block);
    if (!parsed) return;
    if (parsed.event === "meta") handlers.onMeta?.(parsed.data);
    if (parsed.event === "delta") handlers.onDelta?.(parsed.data);
    if (parsed.event === "done") handlers.onDone?.(parsed.data);
    if (parsed.event === "error") handlers.onError?.(parsed.data);
  }

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const blocks = buffer.split(/\r?\n\r?\n/);
    buffer = blocks.pop() || "";
    for (const block of blocks) {
      await flushBlock(block);
    }
  }

  buffer += decoder.decode();
  if (buffer.trim()) {
    await flushBlock(buffer);
  }
}

export async function getDocumentStatus(documentId) {
  const response = await fetch(`${API_BASE_URL}/api/documents/${documentId}/status`);
  return parseResponse(response);
}
