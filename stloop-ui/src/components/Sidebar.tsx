import { MessageCircle, Plus, Trash2, Settings, Cpu } from 'lucide-react';
import './Sidebar.css';

interface Project {
  id: string;
  name: string;
  path: string;
  board: string;
  created_at: string;
  status: string;
}

interface SidebarProps {
  projects: Project[];
  currentProject: Project | null;
  onSelectProject: (project: Project | null) => void;
  onDeleteProject: (projectId: string) => void;
  onSettingsClick: () => void;
}

export function Sidebar({ projects, currentProject, onSelectProject, onDeleteProject, onSettingsClick }: SidebarProps) {
  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <div className="logo">
          <Cpu className="logo-icon" />
          <span className="logo-text">STLoop</span>
        </div>
      </div>

      <div className="sidebar-actions">
        <button className="new-project-btn">
          <Plus size={18} />
          <span>新建项目</span>
        </button>
      </div>

      <div className="projects-section">
        <h3 className="section-title">项目历史</h3>
        <div className="projects-list">
          {projects.length === 0 ? (
            <div className="empty-state">
              <MessageCircle size={24} />
              <p>暂无项目</p>
            </div>
          ) : (
            projects.map(project => (
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
                  className="delete-btn"
                  onClick={(e) => {
                    e.stopPropagation();
                    onDeleteProject(project.id);
                  }}
                >
                  <Trash2 size={14} />
                </button>
              </div>
            ))
          )}
        </div>
      </div>

      <div className="sidebar-footer">
        <button className="settings-btn" onClick={onSettingsClick}>
          <Settings size={18} />
          <span>设置</span>
        </button>
      </div>
    </aside>
  );
}
