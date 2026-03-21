import React, { useState } from 'react';
import { Send, Cpu } from 'lucide-react';
import { BOARDS } from '../types';
import './InputBox.css';

interface InputBoxProps {
  onSend: (message: string, board: string) => void;
  disabled?: boolean;
}

export function InputBox({ onSend, disabled }: InputBoxProps) {
  const [input, setInput] = useState('');
  const [selectedBoard, setSelectedBoard] = useState(BOARDS[0].value);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (input.trim() && !disabled) {
      onSend(input.trim(), selectedBoard);
      setInput('');
    }
  };

  return (
    <div className="input-box-container">
      <div className="board-selector">
        <Cpu size={16} />
        <select
          value={selectedBoard}
          onChange={(e) => setSelectedBoard(e.target.value)}
          disabled={disabled}
        >
          {BOARDS.map((board) => (
            <option key={board.value} value={board.value}>
              {board.label}
            </option>
          ))}
        </select>
      </div>

      <form className="input-form" onSubmit={handleSubmit}>
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="描述你想实现的功能，例如：让 PA5 的 LED 每秒闪烁一次..."
          rows={3}
          disabled={disabled}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault();
              handleSubmit(e);
            }
          }}
        />
        <button
          type="submit"
          className="send-btn"
          disabled={disabled || !input.trim()}
        >
          <Send size={20} />
        </button>
      </form>

      <div className="input-hint">
        <span>按 Enter 发送，Shift + Enter 换行</span>
      </div>
    </div>
  );
}
