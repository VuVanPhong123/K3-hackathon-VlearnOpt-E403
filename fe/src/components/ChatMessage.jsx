export default function ChatMessage({ message, onCitationClick, showDebug = false }) {
  const isAssistant = message.role === "assistant";
  return (
    <article className={isAssistant ? "chat-message assistant" : "chat-message user"}>
      <div className="message-bubble">
        {message.attachment && (
          <div className="message-attachment">
            {message.attachment.filename} - page {message.attachment.pageNumber}
          </div>
        )}
        <p>{message.content}</p>
        {isAssistant && message.provider && <span className="provider-badge">{message.provider}</span>}
        {isAssistant && typeof message.confidence === "number" && message.confidence < 0.35 && (
          <span className="low-confidence">Not enough grounding found in the document.</span>
        )}
        {isAssistant && message.citations?.length > 0 && (
          <div className="citation-row">
            {message.citations.map((citation, index) => {
              const page = citation.page_number || citation.page_start;
              return (
                <button
                  key={`${page || "source"}-${index}`}
                  onClick={() => page && onCitationClick?.(page)}
                  title={page ? `Go to page ${page}` : "Source"}
                >
                  {page ? `page ${page}` : citation.label || "source"}
                </button>
              );
            })}
          </div>
        )}
        {showDebug && isAssistant && message.trace && (
          <details className="debug-panel">
            <summary>Debug</summary>
            <pre>{JSON.stringify({ trace: message.trace, debug: message.debug }, null, 2)}</pre>
          </details>
        )}
      </div>
    </article>
  );
}
