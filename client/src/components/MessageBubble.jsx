export default function MessageBubble({ role, content, sources }) {
  return (
    <div className={`message ${role}`}>
      <div className="message-avatar">
        {role === 'user' ? 'U' : '✦'}
      </div>
      <div className="message-content">
        {content}
        {sources && sources.length > 0 && (
          <div className="message-sources">
            Sources: {sources.map((s) => s.doc_id.substring(0, 8)).join(', ')}
          </div>
        )}
      </div>
    </div>
  );
}
