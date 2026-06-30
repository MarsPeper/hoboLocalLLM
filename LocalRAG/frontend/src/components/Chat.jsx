import React, { useState, useRef, useEffect } from 'react';

export default function Chat() {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: 'Hello! I am your local RAG assistant. Ask me questions about the documents you index in the vector database.',
      sources: []
    }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async (e) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userQuestion = input.trim();
    setInput('');
    setError(null);
    setIsLoading(true);

    // Append user message immediately
    setMessages((prev) => [...prev, { role: 'user', content: userQuestion }]);

    // Append placeholder for assistant response
    setMessages((prev) => [
      ...prev,
      { role: 'assistant', content: '', sources: [], isStreaming: true }
    ]);

    try {
      const response = await fetch('http://localhost:8000/api/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: userQuestion, stream: true }),
      });

      if (!response.ok) {
        throw new Error(`API server responded with status: ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n\n');
        buffer = lines.pop() || ''; // Keep the last incomplete block

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const dataStr = line.slice(6).trim();
            if (dataStr === '[DONE]') {
              break;
            }

            try {
              const parsed = JSON.parse(dataStr);
              if (parsed.type === 'sources') {
                setMessages((prev) => {
                  if (prev.length === 0) return prev;
                  const updated = [...prev];
                  const idx = updated.length - 1;
                  const last = updated[idx];
                  if (last && last.role === 'assistant') {
                    updated[idx] = {
                      ...last,
                      sources: parsed.sources
                    };
                  }
                  return updated;
                });
              } else if (parsed.type === 'token') {
                setMessages((prev) => {
                  if (prev.length === 0) return prev;
                  const updated = [...prev];
                  const idx = updated.length - 1;
                  const last = updated[idx];
                  if (last && last.role === 'assistant') {
                    updated[idx] = {
                      ...last,
                      content: last.content + parsed.token
                    };
                  }
                  return updated;
                });
              } else if (parsed.type === 'error') {
                setError(parsed.message);
              }
            } catch (err) {
              console.error('Failed to parse SSE line:', line, err);
            }
          }
        }
      }
    } catch (err) {
      console.error('Query error:', err);
      setError(err.message || 'Failed to communicate with the local RAG backend.');
      setMessages((prev) => {
        const updated = [...prev];
        const last = updated[updated.length - 1];
        if (last && last.role === 'assistant' && !last.content) {
          last.content = 'Failed to generate response. Check backend connection.';
        }
        return updated;
      });
    } finally {
      setIsLoading(false);
      setMessages((prev) => {
        const updated = [...prev];
        const last = updated[updated.length - 1];
        if (last && last.role === 'assistant') {
          delete last.isStreaming;
        }
        return updated;
      });
    }
  };

  return (
    <div className="chat-container">
      <div className="messages-list">
        {messages.map((msg, idx) => (
          <div key={idx} className={`message-wrapper ${msg.role}`}>
            <div className="message-avatar">
              {msg.role === 'assistant' ? '🤖' : '👤'}
            </div>
            <div className="message-bubble">
              <div className="message-content">
                {msg.content || (msg.isStreaming && !error ? <span className="shimmer-text">Thinking...</span> : '')}
              </div>
              
              {msg.sources && msg.sources.length > 0 && (
                <div className="sources-container">
                  <div className="sources-title">
                    <span>🔍 Retrieved Sources ({msg.sources.length})</span>
                  </div>
                  <div className="sources-list">
                    {msg.sources.map((src, sIdx) => (
                      <details key={sIdx} className="source-item">
                        <summary className="source-summary">
                          <span className="source-file">{src.file_name}</span>
                          <span className="source-meta">
                            Chunk {src.chunk_index + 1} • Match: {(src.score * 100).toFixed(0)}%
                          </span>
                        </summary>
                        <div className="source-detail-content">
                          {src.content}
                        </div>
                      </details>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        ))}
        {error && (
          <div className="error-banner">
            <span>⚠️ Error: {error}</span>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <form onSubmit={handleSend} className="chat-input-form">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask a question about your documents..."
          disabled={isLoading}
          className="chat-input"
        />
        <button type="submit" disabled={isLoading || !input.trim()} className="send-btn">
          {isLoading ? (
            <span className="spinner"></span>
          ) : (
            'Send'
          )}
        </button>
      </form>
    </div>
  );
}
