"""
STLoop 仿真器支持

提供硬件仿真功能：
- Renode: STM32 硬件仿真
- QEMU: 未来支持
"""

from .renode import (
    RenodeSimulator,
    RenodeConfig,
    RenodeStatus,
    find_renode_bin,
    get_platform_file,
    generate_resc_script,
    run as renode_run,
    list_supported_platforms,
)

__all__ = [
    "RenodeSimulator",
    "RenodeConfig",
    "RenodeStatus",
    "find_renode_bin",
    "get_platform_file",
    "generate_resc_script",
    "renode_run",
    "list_supported_platforms",
]
