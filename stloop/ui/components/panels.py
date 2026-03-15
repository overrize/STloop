"""
面板组件 - 信息面板、错误面板、代码面板等
"""

from typing import Optional, Union
from pathlib import Path

from rich.console import Console, RenderableType
from rich.panel import Panel
from rich.text import Text
from rich.syntax import Syntax
from rich.table import Table
from rich import box

from ..console import get_console


def create_info_panel(
    content: RenderableType,
    title: Optional[str] = None,
    console: Console = None,
) -> Panel:
    """
    创建信息面板

    Args:
        content: 面板内容
        title: 面板标题
        console: Console 实例

    Returns:
        Panel 实例
    """
    return Panel(
        content,
        title=title,
        border_style="cyan",
        box=box.ROUNDED,
        padding=(1, 2),
    )


def create_error_panel(
    message: str,
    title: str = "Error",
    suggestions: Optional[list] = None,
    console: Console = None,
) -> Panel:
    """
    创建错误面板

    Args:
        message: 错误信息
        title: 面板标题
        suggestions: 修复建议列表
        console: Console 实例

    Returns:
        Panel 实例
    """
    content = Text.assemble(
        ("[X] ", "red"),
        (message, "red"),
    )

    if suggestions:
        content.append("\n\n")
        content.append("[!] Suggestions:\n", "yellow")
        for i, sug in enumerate(suggestions, 1):
            content.append(f"  {i}. {sug}\n", "dim")

    return Panel(
        content,
        title=f"[red]{title}[/red]",
        border_style="red",
        box=box.DOUBLE,
        padding=(1, 2),
    )


def create_success_panel(
    message: str,
    title: str = "Success",
    details: Optional[dict] = None,
    console: Console = None,
) -> Panel:
    """
    创建成功面板

    Args:
        message: 成功信息
        title: 面板标题
        details: 详细信息字典
        console: Console 实例

    Returns:
        Panel 实例
    """
    content = Text.assemble(
        ("[OK] ", "green"),
        (message, "green"),
    )

    if details:
        content.append("\n\n")
        for key, value in details.items():
            content.append(f"{key}: ", "cyan")
            content.append(f"{value}\n", "white")

    return Panel(
        content,
        title=f"[green]{title}[/green]",
        border_style="green",
        box=box.ROUNDED,
        padding=(1, 2),
    )


def create_warning_panel(
    message: str,
    title: str = "Warning",
    console: Console = None,
) -> Panel:
    """
    创建警告面板

    Args:
        message: 警告信息
        title: 面板标题
        console: Console 实例

    Returns:
        Panel 实例
    """
    content = Text.assemble(
        ("[!] ", "yellow"),
        (message, "yellow"),
    )

    return Panel(
        content,
        title=f"[yellow]{title}[/yellow]",
        border_style="yellow",
        box=box.ROUNDED,
        padding=(1, 2),
    )


def create_code_panel(
    code: str,
    language: str = "c",
    title: Optional[str] = None,
    line_numbers: bool = True,
    console: Console = None,
) -> Panel:
    """
    创建代码显示面板

    Args:
        code: 代码内容
        language: 编程语言（用于语法高亮）
        title: 面板标题
        line_numbers: 是否显示行号
        console: Console 实例

    Returns:
        Panel 实例
    """
    syntax = Syntax(
        code,
        language,
        theme="monokai",
        line_numbers=line_numbers,
        word_wrap=True,
    )

    return Panel(
        syntax,
        title=title or f"[cyan]{language.upper()}[/cyan]",
        border_style="dim",
        box=box.ROUNDED,
        padding=(0, 0),
    )


def create_file_panel(
    file_path: Union[str, Path],
    title: Optional[str] = None,
    max_lines: int = 50,
    console: Console = None,
) -> Optional[Panel]:
    """
    创建文件内容面板

    Args:
        file_path: 文件路径
        title: 面板标题（默认使用文件名）
        max_lines: 最大显示行数
        console: Console 实例

    Returns:
        Panel 实例，文件不存在时返回 None
    """
    path = Path(file_path)

    if not path.exists():
        return create_error_panel(
            f"File not found: {path}",
            title="File Error",
        )

    try:
        content = path.read_text(encoding="utf-8")
        lines = content.split("\n")

        if len(lines) > max_lines:
            content = "\n".join(lines[:max_lines])
            content += f"\n\n[dim]... ({len(lines) - max_lines} more lines)[/dim]"

        # 根据扩展名判断语言
        ext = path.suffix.lower()
        language_map = {
            ".c": "c",
            ".h": "c",
            ".cpp": "cpp",
            ".py": "python",
            ".json": "json",
            ".yaml": "yaml",
            ".yml": "yaml",
            ".md": "markdown",
            ".txt": "text",
        }
        language = language_map.get(ext, "text")

        return create_code_panel(
            content,
            language=language,
            title=title or f"📄 {path.name}",
        )

    except Exception as e:
        return create_error_panel(
            f"Failed to read file: {e}",
            title="Read Error",
        )


def create_table_panel(
    data: dict,
    title: Optional[str] = None,
    key_style: str = "cyan",
    value_style: str = "white",
    console: Console = None,
) -> Panel:
    """
    创建键值表格面板

    Args:
        data: 数据字典
        title: 面板标题
        key_style: 键的样式
        value_style: 值的样式
        console: Console 实例

    Returns:
        Panel 实例
    """
    table = Table(
        show_header=False,
        box=box.SIMPLE,
        padding=(0, 2),
    )
    table.add_column(style=key_style)
    table.add_column(style=value_style)

    for key, value in data.items():
        table.add_row(f"{key}:", str(value))

    return Panel(
        table,
        title=title,
        border_style="dim",
        box=box.ROUNDED,
        padding=(1, 1),
    )
