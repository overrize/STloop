"""
Hardware Catalog - 硬件目录选择器

Embedder 风格的交互式 MCU 选择界面。
"""

from typing import List, Optional, Callable
from dataclasses import dataclass

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.align import Align
from rich import box
from rich.prompt import Prompt
from rich.layout import Layout

from stloop.ui.console import get_console
from stloop.hardware.mcu_database import MCUInfo, MCUFamily, ALL_MCUS, search_mcus, get_mcu


@dataclass
class CatalogConfig:
    """Catalog 配置"""

    show_peripherals: bool = True
    show_memory: bool = True
    max_display: int = 10
    search_enabled: bool = True


class HardwareCatalog:
    """
    硬件目录选择器

    提供交互式 MCU 选择界面，支持：
    - 键盘导航 (↑↓)
    - 实时搜索过滤
    - 外设状态可视化
    - 详细信息展示
    """

    # 外设显示顺序和图标
    PERIPHERAL_ORDER = [
        ("UART", "UART"),
        ("SPI", "SPI"),
        ("I2C", "I2C"),
        ("ADC", "ADC"),
        ("TIM", "TIM"),
        ("DMA", "DMA"),
        ("USB", "USB"),
        ("ETH", "ETH"),
        ("CAN", "CAN"),
        ("WiFi", "WiFi"),
        ("BT", "BT"),
    ]

    def __init__(
        self,
        console: Optional[Console] = None,
        config: Optional[CatalogConfig] = None,
    ):
        self.console = console or get_console()
        self.config = config or CatalogConfig()

        self.mcus = list(ALL_MCUS)
        self.filtered_mcus = self.mcus
        self.selected_idx = 0
        self.search_term = ""

    def filter(self, query: str) -> None:
        """
        根据搜索词过滤 MCU

        Args:
            query: 搜索关键词
        """
        self.search_term = query
        if not query:
            self.filtered_mcus = self.mcus
        else:
            self.filtered_mcus = search_mcus(query)

        # 重置选择位置
        self.selected_idx = 0

    def navigate(self, direction: str) -> bool:
        """
        导航

        Args:
            direction: 'up', 'down', 'first', 'last'

        Returns:
            是否成功导航
        """
        if not self.filtered_mcus:
            return False

        if direction == "up":
            self.selected_idx = max(0, self.selected_idx - 1)
        elif direction == "down":
            self.selected_idx = min(len(self.filtered_mcus) - 1, self.selected_idx + 1)
        elif direction == "first":
            self.selected_idx = 0
        elif direction == "last":
            self.selected_idx = len(self.filtered_mcus) - 1
        else:
            return False

        return True

    def get_selected(self) -> Optional[MCUInfo]:
        """获取当前选中的 MCU"""
        if 0 <= self.selected_idx < len(self.filtered_mcus):
            return self.filtered_mcus[self.selected_idx]
        return None

    def _render_peripherals(self, mcu: MCUInfo) -> str:
        """渲染外设状态"""
        periph_map = {p.name: p for p in mcu.peripherals}

        parts = []
        for name, label in self.PERIPHERAL_ORDER:
            if name in periph_map and periph_map[name].available:
                parts.append(f"[green]{label}[/green]")
            else:
                parts.append(f"[dim]{label}[/dim]")

        return " ".join(parts)

    def _render_memory(self, mcu: MCUInfo) -> str:
        """渲染内存信息"""
        flash_str = f"{mcu.flash_kb // 1024}MB" if mcu.flash_kb >= 1024 else f"{mcu.flash_kb}KB"
        ram_str = f"{mcu.ram_kb // 1024}MB" if mcu.ram_kb >= 1024 else f"{mcu.ram_kb}KB"
        return f"[cyan]{flash_str}[/cyan] / [green]{ram_str}[/green]"

    def render(self) -> Table:
        """
        渲染目录表格

        Returns:
            Rich Table 对象
        """
        table = Table(
            title=f"Hardware Catalog ({len(self.filtered_mcus)} devices)",
            title_style="bold cyan",
            border_style="cyan",
            box=box.ROUNDED,
            show_header=True,
            header_style="bold cyan",
            padding=(0, 1),
        )

        # 列定义
        table.add_column("", width=3, justify="center")  # 选择标记
        table.add_column("MCU", style="cyan", min_width=20)
        table.add_column("Core", style="white", min_width=25)
        table.add_column("Package", style="dim", min_width=12)

        if self.config.show_memory:
            table.add_column("Flash/RAM", min_width=15)

        if self.config.show_peripherals:
            table.add_column("Peripherals", min_width=40)

        # 渲染行
        for i, mcu in enumerate(self.filtered_mcus[: self.config.max_display]):
            # 选择标记
            if i == self.selected_idx:
                marker = "[bold cyan]>[/bold cyan]"
                row_style = "cyan"
            else:
                marker = ""
                row_style = ""

            # MCU 名称（带系列标识）
            family_emoji = {
                MCUFamily.STM32: "[ST]",
                MCUFamily.ESP32: "[ES]",
                MCUFamily.NRF52: "[nR]",
                MCUFamily.RP2: "[RP]",
            }.get(mcu.family, "[  ]")

            mcu_name = f"{family_emoji} {mcu.name}"

            # 核心信息
            core_info = f"{mcu.core.value} @ {mcu.frequency_mhz}MHz"

            row_data = [
                marker,
                mcu_name,
                core_info,
                mcu.package,
            ]

            if self.config.show_memory:
                row_data.append(self._render_memory(mcu))

            if self.config.show_peripherals:
                row_data.append(self._render_peripherals(mcu))

            table.add_row(*row_data, style=row_style)

        # 如果还有更多
        if len(self.filtered_mcus) > self.config.max_display:
            remaining = len(self.filtered_mcus) - self.config.max_display
            table.add_row(
                "",
                f"[dim]... and {remaining} more[/dim]",
                "",
                "",
                "",
                "",
            )

        return table

    def render_details(self, mcu: MCUInfo) -> Panel:
        """
        渲染 MCU 详细信息面板

        Args:
            mcu: MCU 信息

        Returns:
            Rich Panel 对象
        """
        content = []

        # 基本信息
        content.append(f"[bold cyan]{mcu.name}[/bold cyan]")
        content.append(f"[dim]{mcu.description}[/dim]")
        content.append("")

        # 规格
        content.append("[bold]Specifications:[/bold]")
        content.append(f"  Core: [cyan]{mcu.core.value}[/cyan]")
        content.append(f"  Frequency: [cyan]{mcu.frequency_mhz} MHz[/cyan]")
        content.append(f"  Package: [cyan]{mcu.package}[/cyan]")
        content.append(f"  Flash: [cyan]{mcu.flash_kb} KB[/cyan]")
        content.append(f"  RAM: [green]{mcu.ram_kb} KB[/green]")
        content.append("")

        # 外设详情
        content.append("[bold]Peripherals:[/bold]")
        for periph in mcu.peripherals:
            if periph.available:
                status = "[green][OK][/green]"
                desc = f"{periph.name}"
                if periph.count > 1:
                    desc += f" x{periph.count}"
                if periph.description:
                    desc += f" - [dim]{periph.description}[/dim]"
            else:
                status = "[dim][-][/dim]"
                desc = f"[dim]{periph.name}[/dim]"

            content.append(f"  {status} {desc}")

        content.append("")

        # 支持的平台
        support = []
        if mcu.supports_cmsis:
            support.append("CMSIS")
        if mcu.supports_hal:
            support.append("HAL")
        if mcu.supports_zephyr:
            support.append("Zephyr")
        if mcu.supports_arduino:
            support.append("Arduino")

        if support:
            content.append(f"[bold]Supported Frameworks:[/bold] [cyan]{', '.join(support)}[/cyan]")

        return Panel(
            "\n".join(content),
            title="[bold]Device Details[/bold]",
            border_style="cyan",
            box=box.ROUNDED,
            padding=(1, 2),
        )

    def show(self) -> Optional[MCUInfo]:
        """
        显示交互式目录并返回选择结果

        Returns:
            选中的 MCU，取消时返回 None
        """
        self.console.clear()

        # 显示目录
        self.console.print(self.render())
        self.console.print()

        # 显示帮助
        help_text = "[dim]Navigate: ↑/↓ or k/j | Search: / | Select: Enter | Cancel: q[/dim]"
        self.console.print(help_text)
        self.console.print()

        # 简单输入模式（非全交互）
        if self.config.search_enabled and len(self.filtered_mcus) > 5:
            search = Prompt.ask(
                "[cyan]Search[/cyan] (or Enter to list all)",
                default="",
                show_default=False,
            )
            if search:
                self.filter(search)
                return self.show()

        # 选择索引
        if len(self.filtered_mcus) > 0:
            choice = Prompt.ask(
                "[cyan]Select[/cyan] (number or name)",
                default="1",
            )

            # 尝试解析为索引
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(self.filtered_mcus):
                    return self.filtered_mcus[idx]
            except ValueError:
                # 尝试按名称匹配
                mcu = get_mcu(choice.upper())
                if mcu:
                    return mcu

        return None

    def select_interactive(self) -> Optional[MCUInfo]:
        """
        完全交互式选择

        支持键盘导航和搜索。

        Returns:
            选中的 MCU
        """
        while True:
            self.console.clear()

            # 渲染目录和详情
            layout = Layout()
            layout.split_column(
                Layout(self.render(), size=len(self.filtered_mcus) + 5),
                Layout(),
            )

            # 显示选中项详情
            selected = self.get_selected()
            if selected:
                layout.split_row(
                    layout.children[0],
                    Layout(self.render_details(selected), size=50),
                )

            self.console.print(layout)

            # 提示输入
            self.console.print()
            self.console.print("[dim]↑/↓: Navigate | /: Search | Enter: Select | q: Cancel[/dim]")

            # 读取输入（简化版，实际应该读取单个按键）
            cmd = Prompt.ask(
                "[cyan]Command[/cyan]",
                choices=["up", "down", "search", "select", "cancel"],
                default="select",
                show_choices=False,
            )

            if cmd == "up":
                self.navigate("up")
            elif cmd == "down":
                self.navigate("down")
            elif cmd == "search":
                query = Prompt.ask("Search term")
                self.filter(query)
            elif cmd == "select":
                return self.get_selected()
            elif cmd == "cancel":
                return None


def select_mcu(
    console: Optional[Console] = None,
    family: Optional[MCUFamily] = None,
) -> Optional[MCUInfo]:
    """
    便捷函数：选择 MCU

    Args:
        console: Console 实例
        family: 限定 MCU 系列

    Returns:
        选中的 MCU
    """
    console = console or get_console()

    catalog = HardwareCatalog(console)

    if family:
        catalog.mcus = [mcu for mcu in ALL_MCUS if mcu.family == family]
        catalog.filtered_mcus = catalog.mcus

    return catalog.show()
