import React, { useRef, useEffect } from 'react';
import { Message } from '../types';
import './Chat.css';

interface ChatProps {
  messages: Message[];
}

export function Chat({ messages }: ChatProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <div className="chat-container">
      <div className="messages">
        {messages.map((message) => (
          <div
            key={message.id}
            className={`message ${message.role}`}
          >
            <div className="message-avatar">
              {message.role === 'assistant' ? '🤖' : '👤'}
            </div>
            <div className="message-content">
              {message.isLoading ? (
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
