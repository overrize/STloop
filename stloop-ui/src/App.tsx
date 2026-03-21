import React, { useState, useEffect } from 'react';
import { invoke } from '@tauri-apps/api/tauri';
import { Sidebar } from './components/Sidebar';
import { Chat } from './components/Chat';
import { InputBox } from './components/InputBox';
import { SettingsModal } from './components/SettingsModal';
import './App.css';

interface ProjectInfo {
  id: string;
  name: string;
  path: string;
  board: string;
  created_at: string;
  status: string;
}

interface Message {
  role: 'user' | 'assistant';
  content: string;
  loading?: boolean;
}

function App() {
  const [projects, setProjects] = useState<ProjectInfo[]>([]);
  const [currentProject, setCurrentProject] = useState<ProjectInfo | null>(null);
  const [messages, setMessages] = useState<Message[]>([
    {
      role: 'assistant',
      content: '你好！我是 STLoop，你的 Zephyr RTOS 开发助手。描述你想实现的功能，我来帮你生成代码。'
    }
  ]);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);

  useEffect(() => {
    loadProjects();
  }, []);

  const loadProjects = async () => {
    try {
      const projectList = await invoke<ProjectInfo[]>('list_projects');
      setProjects(projectList);
    } catch (error) {
      console.error('Failed to load projects:', error);
    }
  };

  const handleSendMessage = async (content: string, board: string) => {
    setMessages(prev => [...prev, { role: 'user', content }]);

    setMessages(prev => [...prev, {
      role: 'assistant',
      content: '正在生成项目...',
      loading: true
    }]);

    try {
      const project = await invoke<ProjectInfo>('generate_project', {
        request: {
          prompt: content,
          board: board,
          name: null
        }
      });

      setProjects(prev => [...prev, project]);
      setCurrentProject(project);

      setMessages(prev => prev.slice(0, -1));
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: `✅ 项目 "${project.name}" 已生成！\n\nBoard: ${project.board}\n路径: ${project.path}\n\n你可以：\n1. 点击「构建」编译\n2. 点击「烧录」下载到设备\n3. 点击「仿真」在 Renode 中运行`
      }]);
    } catch (error) {
      setMessages(prev => prev.slice(0, -1));
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: `❌ 生成失败: ${error}`
      }]);
    }
  };

  const handleBuild = async () => {
    if (!currentProject) {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: '请先选择一个项目'
      }]);
      return;
    }

    setMessages(prev => [...prev, {
      role: 'assistant',
      content: `正在构建项目 "${currentProject.name}"...`,
      loading: true
    }]);

    try {
      const result = await invoke<{ success: boolean; elf_path?: string; output: string }>('build_project', {
        projectId: currentProject.id
      });

      setMessages(prev => prev.slice(0, -1));
      if (result.success) {
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: `✅ 构建成功！\n\nELF: ${result.elf_path}\n\n输出:\n${result.output.slice(-500)}`
        }]);
      } else {
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: `❌ 构建失败:\n${result.output.slice(-1000)}`
        }]);
      }
    } catch (error) {
      setMessages(prev => prev.slice(0, -1));
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: `❌ 构建错误: ${error}`
      }]);
    }
  };

  const handleFlash = async () => {
    if (!currentProject) {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: '请先选择一个项目'
      }]);
      return;
    }

    setMessages(prev => [...prev, {
      role: 'assistant',
      content: `正在烧录项目 "${currentProject.name}"...`,
      loading: true
    }]);

    try {
      await invoke('flash_project', { projectId: currentProject.id });
      setMessages(prev => prev.slice(0, -1));
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: `✅ 烧录成功！程序已下载到设备。`
      }]);
    } catch (error) {
      setMessages(prev => prev.slice(0, -1));
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: `❌ 烧录失败: ${error}`
      }]);
    }
  };

  const handleSimulate = async () => {
    if (!currentProject) {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: '请先选择一个项目'
      }]);
      return;
    }

    setMessages(prev => [...prev, {
      role: 'assistant',
      content: `正在启动仿真...`,
      loading: true
    }]);

    try {
      await invoke('simulate_project', { projectId: currentProject.id });
      setMessages(prev => prev.slice(0, -1));
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: `✅ 仿真已启动。`
      }]);
    } catch (error) {
      setMessages(prev => prev.slice(0, -1));
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: `❌ 仿真失败: ${error}`
      }]);
    }
  };

  const handleDeleteProject = async (projectId: string) => {
    try {
      await invoke('delete_project', { projectId });
      setProjects(prev => prev.filter(p => p.id !== projectId));
      if (currentProject?.id === projectId) {
        setCurrentProject(null);
      }
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: '项目已删除'
      }]);
    } catch (error) {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: `删除失败: ${error}`
      }]);
    }
  };

  return (
    <div className="app">
      <Sidebar
        projects={projects}
        currentProject={currentProject}
        onSelectProject={setCurrentProject}
        onDeleteProject={handleDeleteProject}
        onSettingsClick={() => setIsSettingsOpen(true)}
      />
      <div className="main-content">
        <Chat messages={messages} />
        <InputBox
          onSend={handleSendMessage}
          currentProjectId={currentProject?.id}
          onBuild={handleBuild}
          onFlash={handleFlash}
          onSimulate={handleSimulate}
        />
      </div>
      {isSettingsOpen && (
        <SettingsModal onClose={() => setIsSettingsOpen(false)} />
      )}
    </div>
  );
}

export default App;
