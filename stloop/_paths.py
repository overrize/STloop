"""包内资源路径"""
from pathlib import Path

_PKG = Path(__file__).resolve().parent
ROOT = _PKG.parent  # 项目根（pip install -e .）或 site-packages 父级


def get_templates_dir() -> Path:
    """模板目录：优先包内，否则项目根"""
    tpl = _PKG / "templates"
    return tpl if (tpl / "stm32_ll").exists() else ROOT / "templates"


def get_demos_dir() -> Path:
    """Demo 目录"""
    demos = _PKG / "demos"
    return demos if demos.exists() else ROOT / "demos"


def get_cube_dir() -> Path:
    return ROOT / "cube" / "STM32CubeF4"
