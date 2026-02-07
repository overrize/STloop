"""包内资源路径 — 功能与业务解耦"""
from pathlib import Path

_PKG = Path(__file__).resolve().parent
STLOOP_ROOT = _PKG.parent  # STloop 所在目录
ROOT = STLOOP_ROOT  # 兼容


def get_projects_dir(work_dir: Path | None = None) -> Path:
    """生成项目根目录：与 STloop 同级，便于独立复制/二次开发"""
    wd = Path(work_dir or Path.cwd()).resolve()
    try:
        wd.relative_to(STLOOP_ROOT)
        parent = STLOOP_ROOT.parent
        if len(parent.parts) <= 1 or parent == STLOOP_ROOT:
            return STLOOP_ROOT
        return parent
    except ValueError:
        return wd


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
