function providerLabel(provider, fallbackUsed) {
  if (provider === "openai") return "OpenAI";
  if (provider === "gemini") return fallbackUsed ? "Gemini dự phòng" : "Gemini";
  return "";
}

function decisionLabel(decision) {
  if (decision === "answer") return "Trả lời";
  if (decision === "clarify") return "Yêu cầu làm rõ";
  if (decision === "abstain") return "Không suy đoán";
  return decision;
}

export default function ChatMessage({
  message,
  onCitationClick,
  onRetry,
  showDebug = false,
}) {
  const isAssistant = message.role === "assistant";
  const badge = providerLabel(message.provider, message.fallbackUsed);
  const decision = message.decision || message.trace?.decision;
  const needsClarification =
    message.needsClarification ??
    message.needs_clarification ??
    (decision === "clarify");
  const abstained = message.abstained ?? (decision === "abstain");

  return (
    <article className={isAssistant ? "chat-message assistant" : "chat-message user"}>
      <div className="message-bubble">
        {message.attachment && (
          <div className="message-attachment">
            {message.attachment.filename} - Trang {message.attachment.pageNumber}
            {message.attachment.type === "text_selection" && " - Đoạn văn bản"}
            {message.attachment.type === "visual_region" && " - Vùng hình ảnh"}
          </div>
        )}
        <p>
          {message.content}
          {message.streaming && <span className="stream-cursor" aria-hidden="true">|</span>}
        </p>
        {message.statusText && !message.content && (
          <p className="message-status">{message.statusText}</p>
        )}
        {message.incomplete && (
          <div className="partial-error">
            <span>{message.errorDetail || "Phản hồi bị gián đoạn."}</span>
            <button type="button" onClick={() => onRetry?.(message.retryText || "")}>
              Thử lại
            </button>
          </div>
        )}
        <p>{message.content}</p>
        {isAssistant && needsClarification && (
          <div className="response-state clarification-state" role="status">
            <strong>Cần thêm thông tin</strong>
            <span>Hãy bổ sung chi tiết để Tutor có thể trả lời chính xác hơn.</span>
          </div>
        )}
        {isAssistant && abstained && (
          <div className="response-state abstained-state" role="status">
            <strong>Chưa đủ bằng chứng</strong>
            <span>Tutor đã dừng trả lời để tránh suy đoán ngoài tài liệu.</span>
          </div>
        )}
        {isAssistant && badge && <span className="provider-badge">{badge}</span>}
        {isAssistant && decision && (
          <span className="decision-badge" data-decision={decision}>
            Quyết định: {decisionLabel(decision)}
          </span>
        )}
        {isAssistant && message.citations?.length > 0 && (
          <div className="citation-row">
            {message.citations.map((citation, index) => {
              const page = citation.page_number || citation.page_start;
              return (
                <button
                  key={`${page || "nguon"}-${index}`}
                  onClick={() => page && onCitationClick?.(page)}
                  title={page ? `Đi tới trang ${page}` : "Nguồn tham khảo"}
                >
                  {page ? `Trang ${page}` : citation.label || "Nguồn"}
                </button>
              );
            })}
          </div>
        )}
        {showDebug && isAssistant && message.trace && (
          <details className="debug-panel">
            <summary>Thông tin kỹ thuật</summary>
            <pre>{JSON.stringify({ trace: message.trace, debug: message.debug }, null, 2)}</pre>
          </details>
        )}
      </div>
    </article>
  );
}
