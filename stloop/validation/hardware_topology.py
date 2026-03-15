"""
验证硬件拓扑：目标 MCU 与各接口/设备连接关系

用于在验证视图一侧展示连接示意图。
"""

from dataclasses import dataclass, field
from typing import List

from rich.panel import Panel
from rich.text import Text
from rich import box


@dataclass
class ValidationTopology:
    """验证硬件拓扑：MCU + 连接列表"""
    mcu_name: str = "STM32"
    mcu_subtitle: str = "TARGET MCU"
    connections: List[str] = field(default_factory=lambda: [
        "JTAG",
        "SERIAL",
        "LOGIC ANALYZER",
        "SCOPE",
        "MOTOR",
    ])

    def render(self) -> Text:
        """用 ASCII 框图渲染：中央 MCU，周围连接"""
        t = Text()
        # 第一行：连接设备（上）
        for i, conn in enumerate(self.connections):
            if i > 0:
                t.append("   ", "dim")
            t.append(f" [{conn}] ", "dim")
        t.append("\n")
        # 竖线向下
        n = len(self.connections)
        t.append("    " + "   ".join(" | " for _ in range(n)) + "\n", "dim")
        t.append("    " + "   ".join(" | " for _ in range(n)) + "\n", "dim")
        # 中央 MCU
        t.append("  ┌─────────────────┐\n", "cyan")
        t.append("  │ ", "cyan")
        t.append(self.mcu_name, "bold cyan")
        t.append("             │\n", "cyan")
        t.append("  │ ", "cyan")
        t.append(self.mcu_subtitle, "dim")
        t.append("   │\n", "cyan")
        t.append("  └─────────────────┘\n", "cyan")
        return t

    def render_panel(self, title: str = "Hardware Connections") -> Panel:
        """返回带标题的 Panel"""
        return Panel(
            self.render(),
            title=title,
            border_style="dim",
            box=box.ROUNDED,
            padding=(0, 1),
        )
