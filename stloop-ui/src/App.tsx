import React, { useState, useEffect } from 'react';
import { Sidebar } from './components/Sidebar';
import { Chat } from './components/Chat';
import { InputBox } from './components/InputBox';
import './App.css';

function App() {
  const [projects, setProjects] = useState([]);
  const [currentProject, setCurrentProject] = useState(null);
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: '你好！我是 STLoop，你的 Zephyr RTOS 开发助手。描述你想实现的功能，我来帮你生成代码。'
    }
  ]);

  const handleSendMessage = async (content: string) => {
    setMessages(prev => [...prev, { role: 'user', content }]);
    
    setMessages(prev => [...prev, { 
      role: 'assistant', 
      content: '正在生成项目...',
      loading: true 
    }]);

    // TODO: Call Tauri command to generate project
    setTimeout(() => {
      setMessages(prev => prev.slice(0, -1));
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: '✅ 项目已生成！\\n\\n你可以：\\n1. 点击「构建」编译\\n2. 点击「烧录」下载到设备\\n3. 点击「仿真」在 Renode 中运行'
      }]);
    }, 2000);
  };

  return (
    <div className="app">
      <Sidebar 
        projects={projects} 
        currentProject={currentProject}
        onSelectProject={setCurrentProject}
      />
      <div className="main-content">
        <Chat messages={messages} />
        <InputBox onSend={handleSendMessage} />
      </div>
    </div>
  );
}

export default App;
