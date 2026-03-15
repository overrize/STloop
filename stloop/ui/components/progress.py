"""
进度组件 - 进度条、步骤指示器、Spinner
"""

from typing import Optional, List
from contextlib import contextmanager

from rich.console import Console
from rich.progress import (
    Progress,
    SpinnerColumn,
    BarColumn,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
    MofNCompleteColumn,
)
from rich.live import Live
from rich.tree import Tree
from rich.text import Text
from rich.panel import Panel

from ..console import get_console


def create_progress(
    console: Console = None,
    transient: bool = False,
) -> Progress:
    """
    创建 Embedder 风格的进度条

    Args:
        console: Console 实例
        transient: 完成后是否清除进度条

    Returns:
        Progress 实例
    """
    console = console or get_console()

    return Progress(
        SpinnerColumn(style="cyan"),
        TextColumn("[cyan]{task.description}"),
        BarColumn(
            complete_style="cyan",
            finished_style="green",
            pulse_style="dim cyan",
        ),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        MofNCompleteColumn(),
        TimeElapsedColumn(),
        TimeRemainingColumn(),
        console=console,
        transient=transient,
    )


@contextmanager
def create_spinner(
    message: str,
    console: Console = None,
):
    """
    创建 Spinner 上下文管理器

    使用示例：
        with create_spinner("Loading..."):
            time.sleep(2)

    Args:
        message: 显示的消息
        console: Console 实例

    Yields:
        None
    """
    console = console or get_console()

    progress = Progress(
        SpinnerColumn(style="cyan"),
        TextColumn("[cyan]{task.description}"),
        console=console,
        transient=True,
    )

    task = progress.add_task(message, total=None)

    try:
        progress.start()
        yield progress
    finally:
        progress.stop()


class StepIndicator:
    """
    多步骤流程指示器

    显示当前执行到哪一步，以及各步骤的状态。

    使用示例：
        steps = ["Parse", "Generate", "Compile", "Flash"]
        indicator = StepIndicator(steps)

        for step in steps:
            indicator.next()
            # 执行步骤...
    """

    def __init__(
        self,
        steps: List[str],
        console: Console = None,
    ):
        """
        初始化步骤指示器

        Args:
            steps: 步骤名称列表
            console: Console 实例
        """
        self.steps = steps
        self.current = 0
        self.console = console or get_console()
        self.completed = []

    def next(self, success: bool = True) -> None:
        """
        进入下一步

        Args:
            success: 当前步骤是否成功完成
        """
        if self.current < len(self.steps):
            if success:
                self.completed.append(self.steps[self.current])
            self.current += 1
        self.render()

    def render(self) -> None:
        """渲染当前状态"""
        tree = Tree(">>> Progress", style="cyan")

        for i, step in enumerate(self.steps):
            if i < len(self.completed):
                # 已完成
                tree.add(f"[green][OK][/green] {step}", style="dim")
            elif i == self.current:
                # 当前步骤
                tree.add(f"[cyan][>][/cyan] [bold cyan]{step}[/bold cyan]", style="cyan")
            else:
                # 未开始
                tree.add(f"[dim][ ] {step}[/dim]", style="dim")

        self.console.print(tree)

    def is_complete(self) -> bool:
        """检查是否所有步骤都已完成"""
        return self.current >= len(self.steps)

    def get_current_step(self) -> Optional[str]:
        """获取当前步骤名称"""
        if self.current < len(self.steps):
            return self.steps[self.current]
        return None


class WorkflowDisplay:
    """
    工作流显示组件

    显示复杂工作流的实时状态，支持并行任务。
    """

    def __init__(self, console: Console = None):
        """
        初始化工作流显示器

        Args:
            console: Console 实例
        """
        self.console = console or get_console()
        self.tasks = {}

    def add_task(
        self,
        task_id: str,
        description: str,
        status: str = "pending",
    ) -> None:
        """
        添加任务

        Args:
            task_id: 任务唯一标识
            description: 任务描述
            status: 初始状态 (pending/running/success/error)
        """
        self.tasks[task_id] = {
            "description": description,
            "status": status,
            "details": "",
        }

    def update_task(
        self,
        task_id: str,
        status: Optional[str] = None,
        details: Optional[str] = None,
    ) -> None:
        """
        更新任务状态

        Args:
            task_id: 任务标识
            status: 新状态
            details: 详细信息
        """
        if task_id in self.tasks:
            if status:
                self.tasks[task_id]["status"] = status
            if details:
                self.tasks[task_id]["details"] = details

    def render(self) -> Panel:
        """
        渲染工作流状态

        Returns:
            Panel 实例
        """
        status_icons = {
            "pending": "[ ]",
            "running": "[*]",
            "success": "[OK]",
            "error": "[X]",
        }

        status_styles = {
            "pending": "dim",
            "running": "cyan",
            "success": "green",
            "error": "red",
        }

        content = []
        for task_id, task in self.tasks.items():
            icon = status_icons.get(task["status"], "?")
            style = status_styles.get(task["status"], "white")

            line = f"[{style}]{icon}[/{style}] {task['description']}"
            if task["details"]:
                line += f"\n   [dim]{task['details']}[/dim]"

            content.append(line)

        return Panel(
            "\n".join(content),
            title="[cyan]Workflow[/cyan]",
            border_style="cyan",
        )

    def print(self) -> None:
        """打印工作流状态"""
        self.console.print(self.render())


class BuildProgress:
    """
    构建进度显示器

    专门用于显示编译过程的进度。
    """

    def __init__(
        self,
        total_steps: int,
        console: Console = None,
    ):
        """
        初始化构建进度

        Args:
            total_steps: 总步骤数
            console: Console 实例
        """
        self.total = total_steps
        self.current = 0
        self.console = console or get_console()
        self.progress = create_progress(console)
        self.task = None

    def __enter__(self):
        """上下文管理器入口"""
        self.progress.start()
        self.task = self.progress.add_task(
            "Building...",
            total=self.total,
        )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.progress.stop()

    def advance(self, message: str = "") -> None:
        """
        前进一步

        Args:
            message: 更新的消息
        """
        self.current += 1
        if message:
            self.progress.update(self.task, description=message)
        self.progress.advance(self.task)

    def set_message(self, message: str) -> None:
        """
        设置当前消息

        Args:
            message: 消息内容
        """
        self.progress.update(self.task, description=message)
