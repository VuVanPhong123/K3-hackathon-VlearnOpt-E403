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

export async function sendChat(payload) {
  const response = await fetch(`${API_BASE_URL}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return parseResponse(response);
}

export async function sendChatV2(payload) {
  const response = await fetch(`${API_BASE_URL}/api/v2/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return parseResponse(response);
}

export async function getDocumentStatus(documentId) {
  const response = await fetch(`${API_BASE_URL}/api/documents/${documentId}/status`);
  return parseResponse(response);
}
