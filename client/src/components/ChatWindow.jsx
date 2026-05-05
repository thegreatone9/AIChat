import { useRef, useEffect } from 'react';
import MessageBubble from './MessageBubble';
import ChatInput from './ChatInput';

export default function ChatWindow({ messages, loading, onSend }) {
  const messagesEndRef = useRef(null);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  return (
    <div className="chat-area">
      <div className="chat-header">
        <h1>AIChat</h1>
        <span className="chat-header-sub">Knowledge-powered assistant</span>
      </div>

      <div className="chat-messages">
        {messages.length === 0 && !loading ? (
          <div className="chat-empty">
            <div className="chat-empty-icon">✦</div>
            <h2>Ask me anything</h2>
            <p>
              Upload documents to the knowledge base, then ask questions.
              I'll find answers from your documents.
            </p>
          </div>
        ) : (
          <>
            {messages.map((msg, idx) => (
              <MessageBubble
                key={idx}
                role={msg.role}
                content={msg.content}
                sources={msg.sources}
              />
            ))}

            {loading && (
              <div className="message assistant">
                <div className="message-avatar">✦</div>
                <div className="message-content">
                  <div className="typing-indicator">
                    <span />
                    <span />
                    <span />
                  </div>
                </div>
              </div>
            )}
          </>
        )}
        <div ref={messagesEndRef} />
      </div>

      <ChatInput onSend={onSend} disabled={loading} />
    </div>
  );
}
