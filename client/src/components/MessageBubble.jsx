import { useState } from 'react';

export default function MessageBubble({ role, content, sources }) {
  const [showSources, setShowSources] = useState(false);

  const hasSources = sources && sources.length > 0;

  return (
    <div className={`message ${role}`}>
      <div className="message-avatar">
        {role === 'user' ? 'U' : '✦'}
      </div>
      <div className="message-content">
        {content}

        {hasSources && (
          <div className="message-sources-section">
            <button
              className="sources-toggle"
              onClick={() => setShowSources(!showSources)}
            >
              {showSources ? '▾' : '▸'} {sources.length} source{sources.length !== 1 ? 's' : ''} referenced
            </button>

            {showSources && (
              <div className="sources-list">
                {sources.map((s, i) => (
                  <div key={i} className="source-item">
                    <div className="source-header">
                      <span className="source-badge">Chunk #{s.chunk_index + 1}</span>
                      <span className="source-score">
                        {Math.round((1 - s.score) * 100)}% match
                      </span>
                    </div>
                    <div className="source-excerpt">
                      "{s.excerpt}..."
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
