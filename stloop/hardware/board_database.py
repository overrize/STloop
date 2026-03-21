"""
Board 数据库 - Zephyr Only

Zephyr 使用 board 文件而非直接管理 MCU 寄存器
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Board:
    """Zephyr Board 信息"""

    name: str  # Zephyr board 名 (如 nucleo_f411re)
    display_name: str  # 显示名 (如 "Nucleo F411RE")
    mcu: str  # MCU 型号 (如 "STM32F411RE")
    arch: str  # 架构 (如 "arm")
    has_renode: bool = False  # 是否支持 Renode 仿真
    renode_platform: Optional[str] = None  # Renode 平台文件


# 支持的 Board 列表
SUPPORTED_BOARDS: dict[str, Board] = {
    "nucleo_f411re": Board(
        name="nucleo_f411re",
        display_name="STM32 Nucleo F411RE",
        mcu="STM32F411RE",
        arch="arm",
        has_renode=True,
        renode_platform="platforms/cpus/stm32f4.repl",
    ),
    "nucleo_f401re": Board(
        name="nucleo_f401re",
        display_name="STM32 Nucleo F401RE",
        mcu="STM32F401RE",
        arch="arm",
        has_renode=True,
        renode_platform="platforms/cpus/stm32f4.repl",
    ),
    "nucleo_f446re": Board(
        name="nucleo_f446re",
        display_name="STM32 Nucleo F446RE",
        mcu="STM32F446RE",
        arch="arm",
        has_renode=True,
        renode_platform="platforms/cpus/stm32f4.repl",
    ),
    "stm32f4_disco": Board(
        name="stm32f4_disco",
        display_name="STM32F4 Discovery",
        mcu="STM32F407VG",
        arch="arm",
        has_renode=True,
        renode_platform="platforms/cpus/stm32f4.repl",
    ),
    "nucleo_f429zi": Board(
        name="nucleo_f429zi",
        display_name="STM32 Nucleo F429ZI",
        mcu="STM32F429ZI",
        arch="arm",
        has_renode=True,
        renode_platform="platforms/cpus/stm32f4.repl",
    ),
}


def get_board(name: str) -> Optional[Board]:
    """获取 Board 信息"""
    return SUPPORTED_BOARDS.get(name.lower())


def list_boards() -> list[Board]:
    """列出所有支持的 Board"""
    return list(SUPPORTED_BOARDS.values())


def infer_board(prompt: str) -> str:
    """从用户输入推断 Board，默认 nucleo_f411re"""
    prompt_lower = prompt.lower()

    # 直接匹配 board 名
    for board_name in SUPPORTED_BOARDS:
        if board_name.replace("_", "") in prompt_lower.replace(" ", ""):
            return board_name

    # 匹配 MCU 型号
    mcu_to_board = {
        "f411": "nucleo_f411re",
        "f401": "nucleo_f401re",
        "f446": "nucleo_f446re",
        "f407": "stm32f4_disco",
        "f429": "nucleo_f429zi",
    }

    for mcu, board in mcu_to_board.items():
        if mcu in prompt_lower:
            return board

    return "nucleo_f411re"  # 默认
