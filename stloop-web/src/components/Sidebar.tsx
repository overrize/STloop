import React from 'react';
import { Folder, Download, Trash2, Plus } from 'lucide-react';
import { Project } from '../types';
import './Sidebar.css';

interface SidebarProps {
  projects: Project[];
  currentProject: Project | null;
  onSelectProject: (project: Project | null) => void;
  onExportProject: (project: Project) => void;
}

export function Sidebar({ 
  projects, 
  currentProject, 
  onSelectProject,
  onExportProject 
}: SidebarProps) {
  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <button 
          className="new-project-btn"
          onClick={() => onSelectProject(null)}
        >
          <Plus size={18} />
          <span>新建项目</span>
        </button>
      </div>

      <div className="projects-section">
        <h3 className="section-title">
          <Folder size={14} />
          项目历史 ({projects.length})
        </h3>
        
        <div className="projects-list">
          {projects.length === 0 ? (
            <div className="empty-state">
              <p>暂无项目</p>
              <span>点击「新建项目」开始</span>
            </div>
          ) : (
            projects.map((project) => (
              <div
                key={project.id}
                className={`project-item ${currentProject?.id === project.id ? 'active' : ''}`}
                onClick={() => onSelectProject(project)}
              >
                <div className="project-info">
                  <span className="project-name">{project.name}</span>
                  <span className="project-board">{project.board}</span>
                </div>
                <button 
                  className="export-btn"
                  onClick={(e) => {
                    e.stopPropagation();
                    onExportProject(project);
                  }}
                  title="导出 ZIP"
                >
                  <Download size={14} />
                </button>
              </div>
            ))
          )}
        </div>
      </div>

      <div className="sidebar-footer">
        <div className="hint">
          <p>💡 提示</p>
          <span>Web 版本无法直接编译和烧录。</span>
          <span>请导出 ZIP 后在本地使用 west 工具。</span>
        </div>
      </div>
    </aside>
  );
}
