"""
Zephyr 项目生成器

简化版 - 只生成 Zephyr 项目
"""

import logging
from pathlib import Path
import shutil
from typing import Optional

from stloop.llm_client import generate_code
from stloop.hardware.board_database import Board, get_board

log = logging.getLogger("stloop")


# Zephyr 项目模板
ZEPHYR_TEMPLATE = """cmake_minimum_required(VERSION 3.20.0)
find_package(Zephyr REQUIRED HINTS $ENV{{ZEPHYR_BASE}})
project(stloop_app)

target_sources(app PRIVATE src/main.c)
"""

# 基础 prj.conf
BASE_PRJ_CONF = """# Zephyr Project Configuration
CONFIG_CONSOLE=y
CONFIG_UART_CONSOLE=y
CONFIG_SERIAL=y
CONFIG_GPIO=y
CONFIG_SYS_CLOCK_HW_CYCLES_PER_SEC=100000000
CONFIG_MAIN_STACK_SIZE=1024
CONFIG_DEBUG=y
"""


class ZephyrProjectGenerator:
    """Zephyr 项目生成器"""

    def __init__(self, template_dir: Optional[Path] = None):
        self.template_dir = template_dir or Path(__file__).parent.parent / "templates" / "zephyr"

    def generate(self, prompt: str, output_dir: Path, board: Optional[str] = None) -> Path:
        """
        生成 Zephyr 项目

        Args:
            prompt: 用户需求描述
            output_dir: 输出目录
            board: Zephyr board 名，None 时自动推断

        Returns:
            项目目录路径
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # 确定 board
        if board is None:
            from stloop.hardware.board_database import infer_board

            board = infer_board(prompt)

        board_info = get_board(board)
        if not board_info:
            raise ValueError(f"不支持的 board: {board}")

        log.info(f"生成 Zephyr 项目: {output_dir} (board: {board})")

        # 创建目录结构
        src_dir = output_dir / "src"
        src_dir.mkdir(exist_ok=True)

        # 生成 main.c
        code = generate_code(prompt, board)
        (src_dir / "main.c").write_text(code, encoding="utf-8")

        # 生成 CMakeLists.txt
        (output_dir / "CMakeLists.txt").write_text(ZEPHYR_TEMPLATE, encoding="utf-8")

        # 生成 prj.conf
        conf = self._generate_conf(prompt)
        (output_dir / "prj.conf").write_text(conf, encoding="utf-8")

        # 保存 board 信息
        (output_dir / ".stloop_board").write_text(board, encoding="utf-8")

        log.info(f"项目生成完成: {output_dir}")
        return output_dir

    def _generate_conf(self, prompt: str) -> str:
        """根据需求生成 prj.conf"""
        conf = BASE_PRJ_CONF.copy()

        prompt_lower = prompt.lower()

        # 根据需求启用功能
        if any(x in prompt_lower for x in ["uart", "serial", "usb"]):
            conf += "\n# UART\nCONFIG_UART_INTERRUPT_DRIVEN=y\n"

        if any(x in prompt_lower for x in ["i2c", "sensor"]):
            conf += "\n# I2C\nCONFIG_I2C=y\n"

        if any(x in prompt_lower for x in ["spi", "flash"]):
            conf += "\n# SPI\nCONFIG_SPI=y\n"

        if any(x in prompt_lower for x in ["pwm", "motor"]):
            conf += "\n# PWM\nCONFIG_PWM=y\n"

        if any(x in prompt_lower for x in ["adc", "analog"]):
            conf += "\n# ADC\nCONFIG_ADC=y\n"

        if any(x in prompt_lower for x in ["bluetooth", "ble", "bt"]):
            conf += "\n# Bluetooth\nCONFIG_BT=y\nCONFIG_BT_PERIPHERAL=y\n"

        if "thread" in prompt_lower or "task" in prompt_lower:
            conf += "\n# Multi-threading\nCONFIG_THREAD_STACK_INFO=y\n"

        return conf
