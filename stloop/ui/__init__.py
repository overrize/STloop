"""
STLoop UI - Embedder 风格的终端界面

提供现代化的终端 UI 组件，包括：
- 主题系统 (theme.py)
- 统一控制台 (console.py)
- 可复用组件 (components/)
- 硬件目录选择器 (hardware_catalog.py)
"""

from .theme import EMBEDDER_THEME, get_theme
from .console import get_console, create_console
from .hardware_catalog import (
    HardwareCatalog,
    select_mcu,
    CatalogConfig,
)
from .serial_monitor import (
    SerialMonitor,
    create_monitor,
    DisplayMode,
    LogLevel,
)
from .validation_view import (
    ValidationView,
    ValidationChannel,
    ValidationStatus,
    ValidationLogEntry,
)

# 便捷导出常用组件
from .components import (
    create_progress,
    create_spinner,
    StepIndicator,
    render_splash,
    render_header,
    create_success_panel,
    create_error_panel,
    create_info_panel,
)

__all__ = [
    # Core
    "EMBEDDER_THEME",
    "get_theme",
    "get_console",
    "create_console",
    # Hardware
    "HardwareCatalog",
    "select_mcu",
    "CatalogConfig",
    # Serial
    "SerialMonitor",
    "create_monitor",
    "DisplayMode",
    "LogLevel",
    # Components (convenience)
    "create_progress",
    "create_spinner",
    "StepIndicator",
    "render_splash",
    "render_header",
    "create_success_panel",
    "create_error_panel",
    "create_info_panel",
    # Validation
    "ValidationView",
    "ValidationChannel",
    "ValidationStatus",
    "ValidationLogEntry",
]
