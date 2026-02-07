"""包内资源路径 — 功能与业务解耦"""
from pathlib import Path

_PKG = Path(__file__).resolve().parent
# STloop 所在目录（开发时=仓库根，安装后=site-packages/stloop 的父级）
STLOOP_ROOT = _PKG.parent


def get_workspace_root(work_dir: Path | None = None) -> Path:
    """
    用户工作区根目录。项目与手册放于此。
    - 若当前在 STloop 目录内：使用 STloop 的父级作为 workspace（项目与 STloop 同级）
    - 若父级为盘符根则退化为 STloop 根
    - 否则使用 work_dir
    """
    wd = Path(work_dir or Path.cwd()).resolve()
    try:
        wd.relative_to(STLOOP_ROOT)
        parent = STLOOP_ROOT.parent
        # 避免使用盘符根（如 C:\）
        if len(parent.parts) <= 1 or parent == STLOOP_ROOT:
            return STLOOP_ROOT
        return parent
    except ValueError:
        return wd if wd.name != "STloop" else wd.parent


def get_projects_dir(work_dir: Path | None = None) -> Path:
    """生成项目的根目录（与 STloop 同级，或在 workspace 下）"""
    return get_workspace_root(work_dir)


def get_manuals_dir(work_dir: Path | None = None) -> Path:
    """预存手册/原理图目录"""
    return get_workspace_root(work_dir) / "manuals"


def get_cube_root(work_dir: Path | None = None) -> Path:
    """Cube 包根目录"""
    return get_workspace_root(work_dir) / "cube"


def get_cube_dir(family: str = "F4", work_dir: Path | None = None) -> Path:
    """指定系列的 Cube 路径"""
    return get_cube_root(work_dir) / f"STM32Cube{family}"


def get_templates_dir() -> Path:
    """模板目录"""
    tpl = _PKG / "templates"
    return tpl if (tpl / "stm32_ll").exists() else STLOOP_ROOT / "templates"


def get_demos_dir() -> Path:
    """Demo 目录"""
    demos = _PKG / "demos"
    return demos if demos.exists() else STLOOP_ROOT / "demos"
