"""
头部组件 - 启动画面、Logo、标题栏 (Embedder 风格)
"""

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.align import Align
from rich import box
from rich.style import Style

from stloop import __version__
from ..console import get_console
from ..theme import BRAND_COLOR, BRAND_DIM


# Embedder 风格的简洁 ASCII Logo
LOGO_FULL = f"""[bold {BRAND_COLOR}]
  ███████╗████████╗██╗      ██████╗  ██████╗ ██████╗ 
  ██╔════╝╚══██╔══╝██║     ██╔═══██╗██╔═══██╗██╔══██╗
  ███████╗   ██║   ██║     ██║   ██║██║   ██║██████╔╝
  ╚════██║   ██║   ██║     ██║   ██║██║   ██║██╔═══╝ 
  ███████║   ██║   ███████╗╚██████╔╝╚██████╔╝██║     
  ╚══════╝   ╚═╝   ╚══════╝ ╚═════╝  ╚═════╝ ╚═╝     
[/bold {BRAND_COLOR}]"""

LOGO_SMALL = f"""[bold {BRAND_COLOR}]
  ╔═══════════════════════════════════════════════════╗
  ║     STLOOP - AI Firmware Engineer                 ║
  ╚═══════════════════════════════════════════════════╝
[/bold {BRAND_COLOR}]"""

# 支持的 MCU 平台
SUPPORTED_PLATFORMS = [
    ("STM32", "Cortex-M"),
    ("ESP32", "Xtensa"),
    ("nRF52", "Cortex-M4"),
    ("RISC-V", "RISC-V"),
    ("RP2040", "Cortex-M0+"),
]


def render_logo(console: Console = None, full: bool = True) -> None:
    """
    渲染 Logo
    """
    console = console or get_console()
    logo = LOGO_FULL if full else LOGO_SMALL
    console.print(logo)


def render_splash(console: Console = None) -> None:
    """
    渲染启动画面 - Embedder 风格
    """
    console = console or get_console()

    # Logo
    console.print(LOGO_FULL)

    # 版本和标语 - 居中对齐
    version_line = Text.assemble(
        (f"v{__version__}", f"bold {BRAND_COLOR}"),
        ("  —  ", "dim"),
        ("AI Firmware Engineer", "dim cyan"),
    )
    console.print(Align.center(version_line))
    console.print()

    # 支持的平台 - 表格风格
    platforms_line = Text()
    for i, (platform, arch) in enumerate(SUPPORTED_PLATFORMS):
        if i > 0:
            platforms_line.append("  │  ", "dim")
        platforms_line.append(platform, "cyan")
        platforms_line.append(f" {arch}", "dim")

    console.print(Align.center(platforms_line))
    console.print()

    # 状态指示 - 类似 embedder 的 [>] 和 [OK] 标记
    status_line = Text.assemble(
        ("[>", BRAND_COLOR),
        ("] Hardware Intelligence", "cyan"),
        ("    ", ""),
        ("[", ""),
        ("OK", "green"),
        ("] Ready", ""),
    )
    console.print(Align.center(status_line))
    console.print()


def render_header(title: str = "STLoop", subtitle: str = "", console: Console = None) -> None:
    """
    渲染页面头部 - 现代化风格
    """
    console = console or get_console()

    text = Text.assemble(
        ("[> ", BRAND_COLOR),
        (title, f"bold {BRAND_COLOR}"),
    )

    if subtitle:
        text.append(f"  —  {subtitle}", "dim")

    console.print(
        Panel(
            text,
            border_style=BRAND_DIM,
            padding=(0, 2),
            box=box.ROUNDED,
        )
    )


def render_footer(message: str = "", console: Console = None) -> None:
    """
    渲染页面底部
    """
    console = console or get_console()

    if message:
        console.print(
            Panel(
                f"[dim]{message}[/dim]",
                border_style="dim",
                padding=(0, 1),
                box=box.SQUARE,
            )
        )


def render_section_header(title: str, icon: str = "", console: Console = None) -> None:
    """
    渲染章节标题
    """
    console = console or get_console()

    prefix = f"{icon} " if icon else ""
    console.print(f"\n[bold {BRAND_COLOR}]{prefix}{title}[/bold {BRAND_COLOR}]")
    console.print(f"[{BRAND_DIM}]{'─' * (len(title) + len(prefix))}[/]")


def render_status_badge(status: str, label: str = "", console: Console = None) -> None:
    """
    渲染状态徽章 - 类似 embedder 的 [OK] [IDLE] 样式
    """
    console = console or get_console()

    status_colors = {
        "ok": "green",
        "ready": "green",
        "running": "cyan",
        "idle": "dim",
        "error": "red",
        "warning": "yellow",
        "busy": "yellow",
    }

    color = status_colors.get(status.lower(), "white")
    badge = Text.assemble(
        ("[", "dim"),
        (status.upper(), f"bold {color}"),
        ("]", "dim"),
    )

    if label:
        badge.append(f" {label}")

    console.print(badge)


def clear_screen(console: Console = None) -> None:
    """
    清屏
    """
    console = console or get_console()
    console.clear()
