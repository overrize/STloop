"""
统一 Console 实例管理

提供全局 Console 实例，确保整个应用使用一致的主题和配置。
"""

from typing import Optional
from rich.console import Console
from rich.theme import Theme

from .theme import EMBEDDER_THEME, get_theme

# 全局 Console 实例（懒加载）
_console_instance: Optional[Console] = None


def create_console(
    theme: Optional[Theme] = None,
    force_terminal: Optional[bool] = None,
    color_system: Optional[str] = "auto",
    width: Optional[int] = None,
    height: Optional[int] = None,
) -> Console:
    """
    创建新的 Console 实例

    Args:
        theme: 自定义主题，默认使用 EMBEDDER_THEME
        force_terminal: 强制启用终端功能
        color_system: 颜色系统 ("auto", "standard", "256", "truecolor", "windows")
        width: 终端宽度
        height: 终端高度

    Returns:
        配置好的 Console 实例
    """
    return Console(
        theme=theme or get_theme(),
        force_terminal=force_terminal,
        color_system=color_system,
        width=width,
        height=height,
        highlight=True,
        emoji=True,
        emoji_variant="emoji",
    )


def get_console() -> Console:
    """
    获取全局 Console 实例（懒加载）

    首次调用时创建实例，后续调用返回同一实例。
    这是推荐的使用方式。

    Returns:
        全局 Console 实例
    """
    global _console_instance
    if _console_instance is None:
        _console_instance = create_console()
    return _console_instance


def set_console(console: Console) -> None:
    """
    设置全局 Console 实例

    用于注入自定义配置的 Console。

    Args:
        console: 要设置为全局的 Console 实例
    """
    global _console_instance
    _console_instance = console


def reset_console() -> None:
    """重置全局 Console 实例（下次 get_console 会重新创建）"""
    global _console_instance
    _console_instance = None


def is_terminal() -> bool:
    """检查是否在交互式终端中"""
    return get_console().is_terminal


def is_dumb_terminal() -> bool:
    """检查是否是简易终端（不支持高级功能）"""
    return get_console().is_dumb_terminal


def get_terminal_size() -> tuple[int, int]:
    """获取终端大小 (width, height)"""
    console = get_console()
    return console.width, console.height
