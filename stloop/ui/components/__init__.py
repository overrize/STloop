"""
UI 组件集合

提供可复用的界面组件：
- header: 启动画面、Logo、标题
- panels: 各种面板组件
- progress: 进度条和状态指示
"""

from .header import (
    render_splash,
    render_logo,
    render_header,
    render_footer,
    render_section_header,
    clear_screen,
)

from .panels import (
    create_info_panel,
    create_error_panel,
    create_success_panel,
    create_warning_panel,
    create_code_panel,
)

from .progress import (
    create_progress,
    create_spinner,
    StepIndicator,
)

__all__ = [
    # Header
    "render_splash",
    "render_logo",
    "render_header",
    "render_footer",
    "render_section_header",
    "clear_screen",
    # Panels
    "create_info_panel",
    "create_error_panel",
    "create_success_panel",
    "create_warning_panel",
    "create_code_panel",
    # Progress
    "create_progress",
    "create_spinner",
    "StepIndicator",
]
