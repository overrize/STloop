import React, { useState } from 'react';
import { Send, Cpu, Hammer, Play, Zap } from 'lucide-react';
import './InputBox.css';

interface InputBoxProps {
  onSend: (message: string, board: string) => void;
  currentProjectId?: string;
  onBuild: () => void;
  onFlash: () => void;
  onSimulate: () => void;
}

export function InputBox({ onSend, currentProjectId, onBuild, onFlash, onSimulate }: InputBoxProps) {
  const [input, setInput] = useState('');
  const [selectedBoard, setSelectedBoard] = useState('nucleo_f411re');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (input.trim()) {
      onSend(input, selectedBoard);
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
        >
          <option value="nucleo_f411re">Nucleo F411RE</option>
          <option value="nucleo_f401re">Nucleo F401RE</option>
          <option value="nucleo_f446re">Nucleo F446RE</option>
          <option value="stm32f4_disco">STM32F4 Discovery</option>
        </select>
      </div>

      <form className="input-form" onSubmit={handleSubmit}>
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="描述你想实现的功能，例如：让 PA5 的 LED 每秒闪烁一次..."
          rows={3}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault();
              handleSubmit(e);
            }
          }}
        />
        <button type="submit" className="send-btn">
          <Send size={20} />
        </button>
      </form>

      <div className="quick-actions">
        <button
          className="action-btn"
          title="构建"
          onClick={onBuild}
          disabled={!currentProjectId}
        >
          <Hammer size={16} />
          <span>构建</span>
        </button>
        <button
          className="action-btn"
          title="烧录"
          onClick={onFlash}
          disabled={!currentProjectId}
        >
          <Zap size={16} />
          <span>烧录</span>
        </button>
        <button
          className="action-btn"
          title="仿真"
          onClick={onSimulate}
          disabled={!currentProjectId}
        >
          <Play size={16} />
          <span>仿真</span>
        </button>
      </div>
    </div>
  );
}
