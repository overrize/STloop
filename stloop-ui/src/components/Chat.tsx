import React from 'react';
import './Chat.css';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  loading?: boolean;
}

interface ChatProps {
  messages: Message[];
}

export function Chat({ messages }: ChatProps) {
  const messagesEndRef = React.useRef<HTMLDivElement>(null);

  React.useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <div className="chat-container">
      <div className="messages">
        {messages.map((message, index) => (
          <div
            key={index}
            className={`message ${message.role}`}
          >
            <div className="message-avatar">
              {message.role === 'assistant' ? '🤖' : '👤'}
            </div>
            <div className="message-content">
              {message.loading ? (
                <div className="loading-dots">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              ) : (
                <pre className="message-text">{message.content}</pre>
              )}
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>
    </div>
  );
}
