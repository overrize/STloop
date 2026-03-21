import React, { useState, useCallback } from 'react';
import { generateZephyrProject } from './lib/project';
import { exportProjectAsZip } from './lib/export';
import { Message, Project } from './types';
import { Chat } from './components/Chat';
import { InputBox } from './components/InputBox';
import { Sidebar } from './components/Sidebar';
import { Header } from './components/Header';
import './App.css';

const INITIAL_MESSAGE: Message = {
  id: 'welcome',
  role: 'assistant',
  content: '你好！我是 STLoop Web，你的 Zephyr RTOS 开发助手。\n\n我可以帮你：\n1. 📝 生成 Zephyr 代码\n2. 📦 导出项目 ZIP\n3. 💻 在浏览器中编辑代码\n\n**注意**：Web 版本无法直接编译和烧录。请下载 ZIP 后在本地使用 `west build` 命令。',
  timestamp: Date.now(),
};

function App() {
  const [messages, setMessages] = useState<Message[]>([INITIAL_MESSAGE]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [currentProject, setCurrentProject] = useState<Project | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);

  const addMessage = useCallback((message: Omit<Message, 'id' | 'timestamp'>) => {
    const newMessage: Message = {
      ...message,
      id: Math.random().toString(36).substr(2, 9),
      timestamp: Date.now(),
    };
    setMessages((prev) => [...prev, newMessage]);
    return newMessage;
  }, []);

  const handleSendMessage = useCallback(async (content: string, board: string) => {
    addMessage({ role: 'user', content });
    setIsGenerating(true);

    try {
      addMessage({ 
        role: 'assistant', 
        content: `正在生成项目 (${board})...`,
        isLoading: true,
      });

      const project = await generateZephyrProject(content, board);
      
      setMessages((prev) => prev.filter(m => !m.isLoading));
      
      setProjects((prev) => [project, ...prev]);
      setCurrentProject(project);

      addMessage({
        role: 'assistant',
        content: `✅ 项目「${project.name}」已生成！\n\n📁 文件列表：\n${project.files.map(f => `  - ${f.path}`).join('\n')}\n\n💡 下一步：\n1. 点击左侧项目查看代码\n2. 或点击「导出 ZIP」下载到本地\n3. 解压后运行：\n   west build -b ${board}`,
      });
    } catch (error) {
      setMessages((prev) => prev.filter(m => !m.isLoading));
      addMessage({
        role: 'assistant',
        content: `❌ 生成失败：${error instanceof Error ? error.message : '未知错误'}`,
      });
    } finally {
      setIsGenerating(false);
    }
  }, [addMessage]);

  const handleExportProject = useCallback(async (project: Project) => {
    try {
      await exportProjectAsZip(project);
      addMessage({
        role: 'assistant',
        content: `📦 项目「${project.name}」已导出为 ZIP`,
      });
    } catch (error) {
      addMessage({
        role: 'assistant',
        content: `❌ 导出失败：${error instanceof Error ? error.message : '未知错误'}`,
      });
    }
  }, [addMessage]);

  return (
    <div className="app">
      <Header />
      <div className="main-container">
        <Sidebar
          projects={projects}
          currentProject={currentProject}
          onSelectProject={setCurrentProject}
          onExportProject={handleExportProject}
        />
        <div className="content-area">
          {currentProject ? (
            <div className="project-editor">
              <div className="editor-header">
                <h2>{currentProject.name}</h2>
                <span className="board-badge">{currentProject.board}</span>
                <button 
                  className="export-btn"
                  onClick={() => handleExportProject(currentProject)}
                >
                  导出 ZIP
                </button>
              </div>
              <div className="file-tabs">
                {currentProject.files.map((file) => (
                  <div key={file.path} className="file-content">
                    <div className="file-path">{file.path}</div>
                    <pre className="code-block">
                      <code>{file.content}</code>
                    </pre>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <Chat messages={messages} />
          )}
          <InputBox onSend={handleSendMessage} disabled={isGenerating} />
        </div>
      </div>
    </div>
  );
}

export default App;
