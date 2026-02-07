"""芯片系列与 STM32Cube 映射"""
import re
from pathlib import Path
from typing import Optional

# 手册文件名/型号 -> Cube 系列
FAMILY_PATTERNS = [
    (r"stm32f1|stm32f10[0-3]", "F1"),
    (r"stm32f4|stm32f40[0-9]|stm32f41[0-9]|stm32f42[0-9]|stm32f43[0-9]|stm32f46[0-9]|stm32f47[0-9]", "F4"),
    (r"stm32f7|stm32f72[0-9]|stm32f73[0-9]", "F7"),
    (r"stm32h7|stm32h72[0-9]|stm32h73[0-9]", "H7"),
    (r"stm32l4|stm32l43[0-9]|stm32l44[0-9]|stm32l45[0-9]", "L4"),
    (r"stm32g4|stm32g43[0-9]|stm32g47[0-9]", "G4"),
]


def infer_family_from_text(text: str) -> Optional[str]:
    """从文本（自然语言或手册内容）推断芯片系列"""
    lower = text.lower()
    for pattern, family in FAMILY_PATTERNS:
        if re.search(pattern, lower):
            return family
    return None


def infer_family_from_path(path: Path) -> Optional[str]:
    """从手册文件路径推断"""
    return infer_family_from_text(path.stem)


def infer_family(
    prompt: Optional[str] = None,
    datasheet_paths: Optional[list] = None,
) -> str:
    """
    推断 STM32Cube 系列。默认 F4。
    """
    if datasheet_paths:
        for p in datasheet_paths:
            fam = infer_family_from_path(Path(p))
            if fam:
                return fam
    if prompt:
        fam = infer_family_from_text(prompt)
        if fam:
            return fam
    return "F4"  # 默认
