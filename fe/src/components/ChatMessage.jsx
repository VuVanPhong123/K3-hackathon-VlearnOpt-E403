export default function ChatMessage({ message }) {
  const isAssistant = message.role === "assistant";
  return (
    <article className={isAssistant ? "chat-message assistant" : "chat-message user"}>
      <div className="message-bubble">
        {message.attachment && (
          <div className="message-attachment">
            {message.attachment.filename} - Trang {message.attachment.pageNumber}
          </div>
        )}
        <p>{message.content}</p>
        {isAssistant && message.provider && (
          <span className="provider-badge">{message.provider}</span>
        )}
      </div>
    </article>
  );
}
