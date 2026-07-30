import ReactMarkdown from "react-markdown";
import rehypeKatex from "rehype-katex";
import remarkGfm from "remark-gfm";
import remarkMath from "remark-math";

export default function MessageContent({ content, streaming = false }) {
  return (
    <div className="markdown-content">
      <ReactMarkdown
        remarkPlugins={[remarkGfm, remarkMath]}
        rehypePlugins={[rehypeKatex]}
        components={{
          a: ({ node, ...props }) => (
            <a {...props} target="_blank" rel="noreferrer" />
          ),
          code: ({ className, children, ...props }) => {
            const text = String(children ?? "");
            const isBlock = Boolean(className) || text.includes("\n");
            if (!isBlock) {
              return (
                <code className={className} {...props}>
                  {children}
                </code>
              );
            }
            return (
              <pre className="code-block">
                <code className={className} {...props}>
                  {children}
                </code>
              </pre>
            );
          },
          table: ({ node, ...props }) => (
            <div className="table-scroll">
              <table {...props} />
            </div>
          ),
        }}
      >
        {content || ""}
      </ReactMarkdown>
      {streaming && <span className="stream-cursor" aria-hidden="true">|</span>}
    </div>
  );
}
