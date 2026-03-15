"""
Real-World Validation 视图

Embedder 风格的真实世界验证界面：
- 顶部通道选择：SERIAL / JTAG / LA / OSC
- 全局状态指示：TESTING / PASSED / FAILED
- 下方验证日志区域
"""

from collections import deque
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Deque, List, Optional, TYPE_CHECKING

from rich.console import Console, RenderableType
from rich.layout import Layout
from rich.panel import Panel
from rich.text import Text
from rich import box

from .console import get_console
from .theme import BRAND_COLOR

if TYPE_CHECKING:
    from .validation_protocol import ValidationEvent
    from stloop.validation.hardware_topology import ValidationTopology


class ValidationChannel(str, Enum):
    """验证数据通道"""
    SERIAL = "SERIAL"
    JTAG = "JTAG"
    LA = "LA"
    OSC = "OSC"


class ValidationStatus(str, Enum):
    """验证全局状态"""
    IDLE = "IDLE"
    TESTING = "TESTING"
    PASSED = "PASSED"
    FAILED = "FAILED"


@dataclass
class ValidationLogEntry:
    """单条验证日志（原始 + 可选解析事件）"""
    timestamp: datetime
    raw_line: str
    channel: Optional[ValidationChannel] = None
    event: Optional["ValidationEvent"] = None

    def __post_init__(self) -> None:
        if self.timestamp is None:
            self.timestamp = datetime.now()


class ValidationView:
    """
    真实世界验证专用视图

    提供：
    - 顶部通道 Tab：SERIAL | JTAG | LA | OSC
    - 状态指示：TESTING / PASSED / FAILED
    - 验证日志区域（滚动）
    """

    CHANNELS = [
        ValidationChannel.SERIAL,
        ValidationChannel.JTAG,
        ValidationChannel.LA,
        ValidationChannel.OSC,
    ]

    def __init__(
        self,
        console: Optional[Console] = None,
        max_log_entries: int = 500,
        topology: Optional["ValidationTopology"] = None,
    ):
        self.console = console or get_console()
        self.max_log_entries = max_log_entries
        self.log_entries: Deque[ValidationLogEntry] = deque(maxlen=max_log_entries)
        self.active_channel = ValidationChannel.SERIAL
        self.status = ValidationStatus.IDLE
        self._selected_channel_index = 0
        self.tests_passed = 0
        self.tests_failed = 0
        self._parse_log = True
        self.topology = topology

    def set_topology(self, topology: "ValidationTopology") -> None:
        """设置硬件连接拓扑（用于右侧示意图）"""
        self.topology = topology

    def set_status(self, status: ValidationStatus) -> None:
        """设置全局状态"""
        self.status = status

    def set_active_channel(self, channel: ValidationChannel) -> None:
        """设置当前选中的通道"""
        self.active_channel = channel
        try:
            self._selected_channel_index = self.CHANNELS.index(channel)
        except ValueError:
            self._selected_channel_index = 0

    def append_log(self, raw_line: str, channel: Optional[ValidationChannel] = None) -> None:
        """追加一条原始日志（可选解析为验证事件并更新通过/失败计数）"""
        from .validation_protocol import parse_validation_line

        event = parse_validation_line(raw_line) if self._parse_log else None
        if event and event.passed is True:
            self.tests_passed += 1
        if event and event.passed is False:
            self.tests_failed += 1
        entry = ValidationLogEntry(
            timestamp=datetime.now(),
            raw_line=raw_line,
            channel=channel or self.active_channel,
            event=event,
        )
        self.log_entries.append(entry)

    def render_channel_bar(self) -> Text:
        """渲染顶部通道栏：SERIAL | JTAG | LA | OSC"""
        parts: List[tuple[str, str]] = []
        for i, ch in enumerate(self.CHANNELS):
            label = ch.value
            if i == self._selected_channel_index:
                style = "bold cyan"  # 选中
            else:
                style = "dim"
            parts.append((f" {label} ", style))
            if i < len(self.CHANNELS) - 1:
                parts.append(("│", "dim"))
        t = Text()
        for content, style in parts:
            t.append(content, style=style)
        return t

    def render_status_dot(self) -> Text:
        """渲染状态圆点 + 文字（若有测试计数则追加 N/M）"""
        if self.status == ValidationStatus.TESTING:
            t = Text(" ● TESTING ", style="bold yellow")
        elif self.status == ValidationStatus.PASSED:
            t = Text(" ● PASSED ", style="bold green")
        elif self.status == ValidationStatus.FAILED:
            t = Text(" ● FAILED ", style="bold red")
        else:
            t = Text(" ● IDLE ", style="dim")
        total = self.tests_passed + self.tests_failed
        if total > 0:
            t.append(f" • {self.tests_passed}/{total} tests", style="dim")
        return t

    def render_top_bar(self) -> RenderableType:
        """渲染顶部栏：通道 + 状态"""
        left = self.render_channel_bar()
        right = self.render_status_dot()
        # 用 Table 或 Text 拼成一行：左边通道，右边状态
        full = Text()
        full.append(left)
        # 填充空格使状态靠右（简单处理：固定宽度）
        padding = max(0, 50 - len(left.plain))
        full.append(" " * padding, "dim")
        full.append(right)
        return Panel(
            full,
            title="[bold]REAL-WORLD VALIDATION[/bold]",
            subtitle="Embedder connects to serial, SWD/JTAG, logic analyzers, oscilloscopes",
            border_style=BRAND_COLOR,
            box=box.ROUNDED,
            padding=(0, 1),
        )

    def render_log_content(self, max_lines: int = 30) -> Text:
        """渲染日志区域内容（最近 max_lines 条，按验证事件高亮）"""
        lines = list(self.log_entries)[-max_lines:]
        t = Text()
        for entry in lines:
            ts = entry.timestamp.strftime("%H:%M:%S")
            t.append(f"[{ts}] ", "dim")
            if entry.event:
                prefix = entry.event.prefix_text() + " "
                t.append(prefix, entry.event.source_style())
                msg = (entry.event.message or entry.raw_line).strip()
                t.append(msg + "\n", "white")
            else:
                if entry.channel:
                    t.append(entry.channel.value + " ", "dim")
                t.append(entry.raw_line + "\n", "white")
        if not t.plain:
            t.append("No validation output yet.\n", "dim")
        return t

    def render_log_panel(self) -> Panel:
        """渲染日志面板"""
        content = self.render_log_content()
        return Panel(
            content,
            title="Validation Log",
            border_style="dim",
            box=box.ROUNDED,
            padding=(0, 1),
        )

    def render_topology_panel(self) -> Optional[Panel]:
        """渲染硬件连接图面板（右侧），无拓扑时返回 None"""
        if not self.topology:
            return None
        return self.topology.render_panel()

    def render(self, log_lines: int = 30) -> Layout:
        """渲染完整布局：顶部栏 + 下方（日志 | 可选拓扑图）"""
        layout = Layout()
        layout.split_column(
            Layout(self.render_top_bar(), size=5),
            Layout(name="body"),
        )
        body = layout["body"]
        if self.topology:
            body.split_row(
                Layout(self.render_log_panel(), ratio=3),
                Layout(self.render_topology_panel(), ratio=1),
            )
        else:
            body.update(self.render_log_panel())
        return layout

    def print_once(self, log_lines: int = 30) -> None:
        """单次打印整个视图（非 Live）"""
        self.console.print(self.render(log_lines=log_lines))
