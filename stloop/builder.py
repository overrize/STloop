"""Zephyr 构建封装 — 使用 west"""

import logging
import shutil
import subprocess
from pathlib import Path
from typing import Optional

from .errors import BuildError

log = logging.getLogger("stloop")


def build(
    project_dir: Path,
    board: Optional[str] = None,
    build_dir: Optional[Path] = None,
) -> Path:
    """
    使用 west 构建 Zephyr 项目
    
    Returns:
        生成的 ELF 文件路径
    """
    project_dir = Path(project_dir)
    
    # 从项目读取 board（如果没有指定）
    if board is None:
        board_file = project_dir / ".stloop_board"
        if board_file.exists():
            board = board_file.read_text().strip()
        else:
            raise BuildError("未指定 board，且项目未记录 board 信息")
    
    # 构建命令
    cmd = ["west", "build", "-p", "auto", "-b", board, str(project_dir)]
    if build_dir:
        cmd.extend(["-d", str(build_dir)])
    
    log.info("构建命令: %s", " ".join(cmd))
    
    # 执行构建
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        raise BuildError(f"构建失败:\\n{result.stderr}")
    
    # 查找生成的 ELF
    if build_dir:
        elf = build_dir / "zephyr" / "zephyr.elf"
    else:
        elf = project_dir / "build" / "zephyr" / "zephyr.elf"
    
    if not elf.exists():
        raise BuildError(f"未找到生成的 ELF 文件: {elf}")
    
    log.info("构建成功: %s", elf)
    return elf


def flash(build_dir: Optional[Path] = None) -> None:
    """使用 west flash 烧录"""
    cmd = ["west", "flash"]
    if build_dir:
        cmd.extend(["-d", str(build_dir)])
    
    log.info("烧录命令: %s", " ".join(cmd))
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        raise BuildError(f"烧录失败:\\n{result.stderr}")
    
    log.info("烧录成功")


def check_west() -> bool:
    """检查 west 是否可用"""
    return shutil.which("west") is not None
