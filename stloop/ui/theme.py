"""
Embedder 风格的配色主题

灵感来源于 embedder.com 的设计：
- 青色品牌色 (#00D4FF)
- 深色背景适配
- 硬件状态颜色编码
"""

from rich.theme import Theme
from rich.style import Style

# Embedder 品牌色
BRAND_COLOR = "#00D4FF"
BRAND_DIM = "#0088AA"
ACCENT_COLOR = "#FF6B35"

# Embedder 风格主题定义
EMBEDDER_THEME = Theme(
    {
        # === 品牌与基础 ===
        "brand": f"bold {BRAND_COLOR}",
        "brand_dim": BRAND_DIM,
        "accent": ACCENT_COLOR,
        "title": f"bold {BRAND_COLOR}",
        "subtitle": "dim cyan",
        # === 硬件相关 ===
        "mcu": BRAND_COLOR,  # MCU 名称
        "mcu_dim": BRAND_DIM,  # MCU 次要信息
        "core": "white",  # 处理器核心
        "frequency": "yellow",  # 频率
        "package": "dim",  # 封装
        "memory": "green",  # 内存大小
        "peripheral.on": "green",  # 可用外设
        "peripheral.off": "dim",  # 不可用外设
        "peripheral.active": "bold green",  # 正在使用的外设
        "register.name": "cyan",  # 寄存器名
        "register.addr": "dim",  # 寄存器地址
        "register.value": "yellow",  # 寄存器值
        "register.changed": "bold red",  # 变化的寄存器
        # === 接口状态 ===
        "serial": "#3498DB",  # 串口 - 蓝色
        "jtag": "#F39C12",  # JTAG - 橙色
        "swd": "#E67E22",  # SWD - 深橙
        "logic": "#1ABC9C",  # Logic Analyzer - 青色
        "scope": "#9B59B6",  # 示波器 - 紫色
        "interface.connected": "green",  # 已连接
        "interface.disconnected": "red",  # 未连接
        "interface.active": "bold green",  # 活动状态
        # === 代码与输出 ===
        "code": "green",  # 代码文本
        "code.keyword": "magenta",  # 关键字
        "code.function": "cyan",  # 函数名
        "code.comment": "dim green",  # 注释
        "code.string": "yellow",  # 字符串
        "code.number": "blue",  # 数字
        "output.info": "blue",  # 信息输出
        "output.success": "green",  # 成功
        "output.warning": "yellow",  # 警告
        "output.error": "red",  # 错误
        "output.debug": "dim",  # 调试信息
        # === 交互元素 ===
        "prompt": "bold yellow",  # 输入提示
        "cursor": "bold white on cyan",  # 光标
        "selected": "bold cyan",  # 选中项
        "highlight": "bold white",  # 高亮
        "border": BRAND_DIM,  # 边框
        "border.focused": BRAND_COLOR,  # 聚焦边框
        # === 状态指示 ===
        "status.ok": "green",  # 正常
        "status.warn": "yellow",  # 警告
        "status.error": "red",  # 错误
        "status.pending": "yellow",  # 等待中
        "status.running": "cyan",  # 运行中
        # === 日志级别 ===
        "log.debug": "dim",
        "log.info": "blue",
        "log.warning": "yellow",
        "log.error": "red",
        "log.critical": "bold red",
    }
)


def get_theme() -> Theme:
    """获取 Embedder 主题"""
    return EMBEDDER_THEME


# 颜色常量（用于直接引用）
COLORS = {
    "brand": BRAND_COLOR,
    "brand_dim": BRAND_DIM,
    "accent": ACCENT_COLOR,
    "success": "#2ECC71",
    "warning": "#F1C40F",
    "error": "#E74C3C",
    "info": "#3498DB",
    "text": "#ECF0F1",
    "text_dim": "#7F8C8D",
    "panel_bg": "#1A1A2E",
    "border": "#2D3748",
}


def get_color(name: str) -> str:
    """获取颜色值"""
    return COLORS.get(name, "white")
