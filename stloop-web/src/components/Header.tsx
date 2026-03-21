import React from 'react';
import { Cpu, Github, Info } from 'lucide-react';
import './Header.css';

export function Header() {
  return (
    <header className="header">
      <div className="header-left">
        <Cpu className="logo-icon" size={24} />
        <span className="logo-text">STLoop Web</span>
        <span className="version">Beta</span>
      </div>
      <div className="header-right">
        <a 
          href="https://github.com/stloop/stloop" 
          target="_blank" 
          rel="noopener noreferrer"
          className="header-link"
        >
          <Github size={18} />
          <span>GitHub</span>
        </a>
        <button className="header-btn" title="About">
          <Info size={18} />
        </button>
      </div>
    </header>
  );
}
