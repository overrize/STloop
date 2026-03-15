"""Project spec: 从需求中提取结构化约束并持久化。"""
from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Optional

from .chip_config import infer_chip


@dataclass
class ProjectSpec:
    mcu_device: str
    startup_pattern: str
    linker_pattern: str
    peripherals: list[str]
    sensor: Optional[str]
    requirement: str

    def to_prompt_block(self) -> str:
        """将结构化约束编码为模型可读提示片段。"""
        periph = ", ".join(self.peripherals) if self.peripherals else "GPIO"
        sensor = self.sensor or "unknown"
        return (
            "\n\n【结构化约束（必须遵守）】\n"
            f"- MCU_DEVICE: {self.mcu_device}\n"
            f"- STARTUP_PATTERN: {self.startup_pattern}\n"
            f"- LINKER_PATTERN: {self.linker_pattern}\n"
            f"- 主要外设: {periph}\n"
            f"- 目标传感器: {sensor}\n"
            "- 严禁将芯片/传感器替换为其他型号；若信息不足，保留 TODO 并标注缺失项。\n"
        )


def _infer_peripherals(text: str) -> list[str]:
    lower = text.lower()
    mapping = [
        ("gpio", ("gpio", "led", "pa", "pb", "pc", "pd", "pe")),
        ("uart", ("uart", "usart", "串口")),
        ("spi", ("spi",)),
        ("i2c", ("i2c", "iic")),
        ("adc", ("adc", "采样", "模拟")),
        ("pwm", ("pwm",)),
        ("timer", ("timer", "tim", "定时器")),
        ("imu", ("imu", "陀螺仪", "加速度计", "姿态")),
    ]
    found: list[str] = []
    for name, keys in mapping:
        if any(k in lower for k in keys):
            found.append(name)
    return found or ["gpio"]


def _infer_sensor(text: str) -> Optional[str]:
    for token in ("BMI088", "MPU6500", "MPU6050", "ICM42688"):
        if re.search(token, text, re.IGNORECASE):
            return token
    return None


def build_project_spec(
    requirement: str,
    datasheet_paths: Optional[list[Path | str]] = None,
) -> ProjectSpec:
    mcu_device, startup_pattern, linker_pattern = infer_chip(
        prompt=requirement, datasheet_paths=datasheet_paths
    )
    return ProjectSpec(
        mcu_device=mcu_device,
        startup_pattern=startup_pattern,
        linker_pattern=linker_pattern,
        peripherals=_infer_peripherals(requirement),
        sensor=_infer_sensor(requirement),
        requirement=requirement,
    )


def write_project_spec(path: Path, spec: ProjectSpec) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(asdict(spec), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
