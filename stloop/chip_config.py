"""从用户手册或自然语言推断目标芯片，用于动态配置 CMake startup/linker"""
import re
from pathlib import Path
from typing import Optional

# 型号关键字 -> (MCU_DEVICE 宏, startup 匹配, linker 匹配)
# startup: startup_stm32f405xx.s / startup_stm32f411xe.s
# linker: STM32F405RGTx_FLASH.ld / STM32F411RETx_FLASH.ld
CHIP_MAP = [
    (r"stm32f401[cv]?e?", ("STM32F401xC", "f401", "F401")),
    (r"stm32f405", ("STM32F405xx", "f405", "F405")),
    (r"stm32f407", ("STM32F407xx", "f407", "F407")),
    (r"stm32f410", ("STM32F410xx", "f410", "F410")),
    (r"stm32f411", ("STM32F411xE", "f411", "F411")),
    (r"stm32f412[rceg][a-z]?", ("STM32F412xG", "f412", "F412")),
    (r"stm32f413[rch][a-z]?", ("STM32F413xx", "f413", "F413")),
    (r"stm32f427[rg][a-z]?", ("STM32F427xx", "f427", "F427")),
    (r"stm32f429[rg][a-z]?", ("STM32F429xx", "f429", "F429")),
    (r"stm32f437[rg][a-z]?", ("STM32F437xx", "f437", "F437")),
    (r"stm32f439[rg][a-z]?", ("STM32F439xx", "f439", "F439")),
    (r"stm32f446[rce][a-z]?", ("STM32F446xx", "f446", "F446")),
    (r"stm32f469[rg][a-z]?", ("STM32F469xx", "f469", "F469")),
    (r"stm32f479[rg][a-z]?", ("STM32F479xx", "f479", "F479")),
]


def _infer_from_text(text: str) -> Optional[tuple[str, str, str]]:
    lower = text.lower()
    for pattern, cfg in CHIP_MAP:
        if re.search(pattern, lower):
            return cfg
    return None


def infer_chip(
    prompt: Optional[str] = None,
    datasheet_paths: Optional[list[Path | str]] = None,
) -> tuple[str, str, str]:
    """
    从自然语言或手册路径推断芯片配置。
    返回 (MCU_DEVICE, startup_pattern, linker_pattern)，默认 STM32F411xE。
    """
    if datasheet_paths:
        for p in datasheet_paths:
            path = Path(p)
            cfg = _infer_from_text(path.stem)
            if cfg:
                return cfg
    if prompt:
        cfg = _infer_from_text(prompt)
        if cfg:
            return cfg
    return ("STM32F411xE", "f411", "F411")
