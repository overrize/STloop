"""
STLoop 项目记忆与上下文管理系统

功能：
1. 项目描述存储 - 记录用户项目信息、需求、技术栈
2. 会话历史 - 保存对话记录和完成的任务
3. 上下文更新 - 每次交互后自动更新项目状态
4. 继续对话 - 支持断点续传式的交互
5. 任务队列 - 管理和安排待办任务
"""

import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict, field


@dataclass
class ProjectContext:
    """项目上下文信息"""

    # 基本信息
    project_name: str = ""
    description: str = ""  # 项目描述（用户自然语言描述）
    mcu_model: str = ""  # MCU 型号

    # 技术栈
    framework: str = "cube"  # cube 或 zephyr
    hal_version: str = ""
    libraries: List[str] = field(default_factory=list)  # 使用的库

    # 功能特性
    features: List[str] = field(default_factory=list)  # 已实现的功能
    peripherals: List[str] = field(default_factory=list)  # 使用的外设

    # 状态
    current_status: str = "new"  # new, developing, testing, completed
    last_modified: str = field(default_factory=lambda: datetime.now().isoformat())

    # 代码统计
    total_lines: int = 0
    main_modules: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProjectContext":
        return cls(**data)

    def update(self, **kwargs):
        """更新字段并刷新时间戳"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.last_modified = datetime.now().isoformat()


@dataclass
class TaskRecord:
    """任务记录"""

    task_id: str
    description: str
    status: str  # pending, in_progress, completed, failed
    created_at: str
    completed_at: Optional[str] = None
    result_summary: str = ""  # 任务结果摘要
    code_changes: List[str] = field(default_factory=list)  # 修改的文件

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TaskRecord":
        return cls(**data)


@dataclass
class ConversationTurn:
    """对话回合"""

    turn_id: int
    user_input: str
    agent_response: str
    action_taken: str  # 执行的操作类型
    project_context_before: Dict[str, Any]  # 操作前的上下文
    project_context_after: Dict[str, Any]  # 操作后的上下文
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Session:
    """会话记录"""

    session_id: str
    project_context: ProjectContext
    conversation_history: List[ConversationTurn] = field(default_factory=list)
    task_queue: List[TaskRecord] = field(default_factory=list)
    completed_tasks: List[TaskRecord] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_active: str = field(default_factory=lambda: datetime.now().isoformat())

    def add_turn(self, turn: ConversationTurn):
        """添加对话回合"""
        self.conversation_history.append(turn)
        self.last_active = datetime.now().isoformat()

    def add_task(self, task: TaskRecord):
        """添加任务"""
        self.task_queue.append(task)
        self.last_active = datetime.now().isoformat()

    def complete_task(self, task_id: str, result: str, changes: List[str]):
        """完成任务"""
        for i, task in enumerate(self.task_queue):
            if task.task_id == task_id:
                task.status = "completed"
                task.completed_at = datetime.now().isoformat()
                task.result_summary = result
                task.code_changes = changes
                self.completed_tasks.append(task)
                self.task_queue.pop(i)
                self.last_active = datetime.now().isoformat()
                break

    def get_pending_tasks(self) -> List[TaskRecord]:
        """获取待办任务"""
        return [t for t in self.task_queue if t.status in ("pending", "in_progress")]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "project_context": self.project_context.to_dict(),
            "conversation_history": [t.to_dict() for t in self.conversation_history],
            "task_queue": [t.to_dict() for t in self.task_queue],
            "completed_tasks": [t.to_dict() for t in self.completed_tasks],
            "created_at": self.created_at,
            "last_active": self.last_active,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Session":
        return cls(
            session_id=data["session_id"],
            project_context=ProjectContext.from_dict(data["project_context"]),
            conversation_history=[
                ConversationTurn(**t) for t in data.get("conversation_history", [])
            ],
            task_queue=[TaskRecord.from_dict(t) for t in data.get("task_queue", [])],
            completed_tasks=[TaskRecord.from_dict(t) for t in data.get("completed_tasks", [])],
            created_at=data["created_at"],
            last_active=data["last_active"],
        )


class ProjectMemoryManager:
    """
    项目记忆管理器

    职责：
    1. 保存和加载会话
    2. 管理项目上下文
    3. 记录对话历史
    4. 任务队列管理
    """

    MEMORY_DIR = Path.home() / ".stloop" / "memory"

    def __init__(self):
        self.MEMORY_DIR.mkdir(parents=True, exist_ok=True)
        self._current_session: Optional[Session] = None

    def _get_session_path(self, session_id: str) -> Path:
        """获取会话文件路径"""
        return self.MEMORY_DIR / f"{session_id}.json"

    def _generate_session_id(self, project_hint: str = "") -> str:
        """生成会话 ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if project_hint:
            # 从项目描述中提取关键词
            hint_clean = "".join(c if c.isalnum() else "_" for c in project_hint[:20])
            return f"{hint_clean}_{timestamp}"
        return f"session_{timestamp}"

    def create_session(
        self,
        user_description: str,
        project_name: str = "",
        mcu_model: str = "",
    ) -> Session:
        """
        创建新会话

        Args:
            user_description: 用户自然语言描述的项目需求
            project_name: 项目名称（可选）
            mcu_model: MCU 型号（可选，可从描述推断）
        """
        # 从描述提取关键词作为 ID
        session_id = self._generate_session_id(user_description)

        # 如果没有提供项目名称，从描述生成
        if not project_name:
            project_name = self._extract_project_name(user_description)

        context = ProjectContext(
            project_name=project_name,
            description=user_description,
            mcu_model=mcu_model,
        )

        session = Session(
            session_id=session_id,
            project_context=context,
        )

        self._current_session = session
        self._save_session(session)

        return session

    def _extract_project_name(self, description: str) -> str:
        """从描述提取项目名称"""
        # 简单实现：取前 20 个字符，去除特殊字符
        name = description.strip()[:30]
        name = "".join(c if c.isalnum() or c in (" ", "_", "-") else "_" for c in name)
        return name.replace(" ", "_")

    def load_session(self, session_id: str) -> Optional[Session]:
        """加载会话"""
        session_file = self._get_session_path(session_id)
        if not session_file.exists():
            return None

        with open(session_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        session = Session.from_dict(data)
        self._current_session = session
        return session

    def _save_session(self, session: Session):
        """保存会话"""
        session_file = self._get_session_path(session.session_id)
        with open(session_file, "w", encoding="utf-8") as f:
            json.dump(session.to_dict(), f, indent=2, ensure_ascii=False)

    def list_sessions(self, limit: int = 10) -> List[Session]:
        """列出最近的会话"""
        sessions = []
        for f in sorted(
            self.MEMORY_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True
        ):
            if f.name == "active_session.json":
                continue
            with open(f, "r", encoding="utf-8") as file:
                try:
                    data = json.load(file)
                    sessions.append(Session.from_dict(data))
                except:
                    continue
        return sessions[:limit]

    def get_current_session(self) -> Optional[Session]:
        """获取当前会话"""
        return self._current_session

    def update_context(self, **kwargs):
        """更新当前项目的上下文"""
        if self._current_session:
            self._current_session.project_context.update(**kwargs)
            self._save_session(self._current_session)

    def record_interaction(
        self,
        user_input: str,
        agent_response: str,
        action_taken: str = "",
    ) -> ConversationTurn:
        """
        记录一次交互

        每次用户和 agent 对话后调用，保存上下文变化
        """
        if not self._current_session:
            raise RuntimeError("No active session")

        # 记录操作前的上下文
        context_before = self._current_session.project_context.to_dict()

        # 创建对话回合
        turn = ConversationTurn(
            turn_id=len(self._current_session.conversation_history) + 1,
            user_input=user_input,
            agent_response=agent_response,
            action_taken=action_taken,
            project_context_before=context_before,
            project_context_after=context_before.copy(),  # 暂时相同，后续更新
        )

        self._current_session.add_turn(turn)
        self._save_session(self._current_session)

        return turn

    def update_turn_context_after_action(
        self,
        turn: ConversationTurn,
        new_context_changes: Dict[str, Any],
        code_changes: List[str],
    ):
        """
        在操作完成后更新对话回合的上下文

        例如：完成了代码生成后，更新 features、peripherals 等
        """
        # 更新项目上下文
        self.update_context(**new_context_changes)

        # 更新对话回合
        turn.project_context_after = self._current_session.project_context.to_dict()

        # 如果有代码变更，记录到任务
        if code_changes and self._current_session.task_queue:
            current_task = self._current_session.task_queue[-1]
            current_task.code_changes.extend(code_changes)

        self._save_session(self._current_session)

    def add_task(self, description: str) -> TaskRecord:
        """添加新任务"""
        if not self._current_session:
            raise RuntimeError("No active session")

        task = TaskRecord(
            task_id=f"task_{len(self._current_session.task_queue) + len(self._current_session.completed_tasks) + 1}",
            description=description,
            status="pending",
            created_at=datetime.now().isoformat(),
        )

        self._current_session.add_task(task)
        self._save_session(self._current_session)

        return task

    def start_task(self, task_id: str):
        """开始执行任务"""
        if not self._current_session:
            return

        for task in self._current_session.task_queue:
            if task.task_id == task_id:
                task.status = "in_progress"
                self._save_session(self._current_session)
                break

    def complete_task(
        self,
        task_id: str,
        result: str = "",
        code_changes: List[str] = None,
    ):
        """完成任务"""
        if not self._current_session:
            return

        self._current_session.complete_task(
            task_id=task_id,
            result=result,
            changes=code_changes or [],
        )
        self._save_session(self._current_session)

    def get_context_summary(self) -> str:
        """获取当前上下文的摘要（用于提示）"""
        if not self._current_session:
            return "无活跃会话"

        ctx = self._current_session.project_context
        pending = self._current_session.get_pending_tasks()

        summary = f"""
项目: {ctx.project_name}
描述: {ctx.description[:100]}...
状态: {ctx.current_status}
MCU: {ctx.mcu_model or "未指定"}
框架: {ctx.framework}
已实现功能: {", ".join(ctx.features) if ctx.features else "无"}
使用外设: {", ".join(ctx.peripherals) if ctx.peripherals else "未记录"}
待办任务: {len(pending)} 个
"""
        return summary.strip()

    def suggest_next_steps(self) -> List[str]:
        """根据当前上下文建议下一步"""
        if not self._current_session:
            return ["请描述您的项目需求"]

        suggestions = []
        ctx = self._current_session.project_context
        pending = self._current_session.get_pending_tasks()

        # 基于状态的建议
        if ctx.current_status == "new":
            suggestions.append("生成初始代码框架")
            suggestions.append("配置外设和时钟")
        elif ctx.current_status == "developing":
            if "gpio" not in [p.lower() for p in ctx.peripherals]:
                suggestions.append("添加 GPIO 控制")
            if "uart" not in [p.lower() for p in ctx.peripherals]:
                suggestions.append("添加串口输出")
            suggestions.append("编译和仿真测试")

        # 基于待办任务的建议
        if pending:
            suggestions.append(f"继续任务: {pending[0].description}")

        # 通用建议
        suggestions.append("查看项目状态")
        suggestions.append("列出所有任务")

        return suggestions[:5]

    def export_project_summary(self) -> str:
        """导出项目摘要（Markdown 格式）"""
        if not self._current_session:
            return ""

        ctx = self._current_session.project_context

        md = f"""# {ctx.project_name}

## 项目描述
{ctx.description}

## 技术规格
- **MCU**: {ctx.mcu_model or "待确定"}
- **框架**: {ctx.framework}
- **HAL版本**: {ctx.hal_version or "默认"}

## 已实现功能
"""
        if ctx.features:
            for f in ctx.features:
                md += f"- [x] {f}\n"
        else:
            md += "- 暂无\n"

        md += "\n## 使用的外设\n"
        if ctx.peripherals:
            for p in ctx.peripherals:
                md += f"- {p}\n"
        else:
            md += "- 待记录\n"

        md += f"\n## 会话历史\n"
        for turn in self._current_session.conversation_history[-5:]:  # 最近5条
            md += f"\n### {turn.turn_id}. {turn.action_taken or '对话'}\n"
            md += f"**用户**: {turn.user_input[:100]}...\n\n"
            md += f"**Agent**: {turn.agent_response[:200]}...\n"

        return md


# 全局实例（单例）
_memory_manager: Optional[ProjectMemoryManager] = None


def get_memory_manager() -> ProjectMemoryManager:
    """获取全局记忆管理器实例"""
    global _memory_manager
    if _memory_manager is None:
        _memory_manager = ProjectMemoryManager()
    return _memory_manager


# 便捷函数
def create_or_load_session(
    user_description: str,
    session_id: Optional[str] = None,
) -> Session:
    """
    创建新会话或加载已有会话

    如果提供了 session_id，加载该会话
    否则，根据描述创建新会话或询问用户
    """
    manager = get_memory_manager()

    if session_id:
        session = manager.load_session(session_id)
        if session:
            print(f"已加载会话: {session.project_context.project_name}")
            return session
        else:
            print(f"会话 {session_id} 不存在，创建新会话")

    # 检查是否有相似的项目
    similar = find_similar_projects(user_description)
    if similar:
        print("\n发现相似的项目:")
        for i, s in enumerate(similar[:3], 1):
            print(f"  {i}. {s.project_context.project_name}")
            print(f"     {s.project_context.description[:60]}...")
            print(f"     最后更新: {s.last_active[:10]}")
        print("\n输入编号继续项目，或按 Enter 创建新项目:")
        # 实际应用中这里应该有用户输入处理

    # 创建新会话
    session = manager.create_session(user_description)
    print(f"创建新会话: {session.project_context.project_name}")
    print(f"Session ID: {session.session_id}")

    return session


def find_similar_projects(description: str, threshold: float = 0.6) -> List[Session]:
    """
    查找相似的项目

    简单实现：基于关键词匹配
    实际可以用更复杂的语义相似度
    """
    manager = get_memory_manager()
    all_sessions = manager.list_sessions(limit=20)

    # 提取关键词（简单分词）
    keywords = set(description.lower().split())

    scored_sessions = []
    for session in all_sessions:
        session_words = set(session.project_context.description.lower().split())
        # Jaccard 相似度
        intersection = len(keywords & session_words)
        union = len(keywords | session_words)
        if union > 0:
            similarity = intersection / union
            if similarity >= threshold:
                scored_sessions.append((similarity, session))

    # 按相似度排序
    scored_sessions.sort(key=lambda x: x[0], reverse=True)
    return [s for _, s in scored_sessions]


# 示例用法
def demo():
    """演示用法"""
    print("STLoop 项目记忆系统演示")
    print("=" * 50)

    # 1. 创建会话
    session = create_or_load_session("STM32F411RE Nucleo 开发板，PA5 LED 每 500ms 闪烁一次")

    manager = get_memory_manager()

    # 2. 记录交互
    turn = manager.record_interaction(
        user_input="生成 LED 闪烁代码",
        agent_response="已生成代码，使用 PA5 GPIO",
        action_taken="code_generation",
    )

    # 3. 更新上下文
    manager.update_turn_context_after_action(
        turn=turn,
        new_context_changes={
            "mcu_model": "STM32F411RE",
            "peripherals": ["GPIO", "TIM"],
            "features": ["LED blink", "500ms interval"],
            "current_status": "developing",
        },
        code_changes=["src/main.c", "inc/main.h"],
    )

    # 4. 添加任务
    task = manager.add_task("编译并仿真测试")
    print(f"\n添加任务: {task.description}")

    # 5. 获取上下文摘要
    print("\n当前上下文:")
    print(manager.get_context_summary())

    # 6. 建议下一步
    print("\n建议下一步:")
    for i, suggestion in enumerate(manager.suggest_next_steps(), 1):
        print(f"  {i}. {suggestion}")

    # 7. 导出摘要
    print("\n项目摘要 Markdown:")
    print(manager.export_project_summary())


if __name__ == "__main__":
    demo()
