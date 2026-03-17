#!/usr/bin/env python3
"""
Zephyr 项目构建脚本
"""

import subprocess
import sys
from pathlib import Path


def build_zephyr(project_dir: Path, board: str = "nucleo_f411re"):
    """构建 Zephyr 项目"""
    build_dir = project_dir / "build"

    # 设置 Zephyr 环境
    env = {
        "ZEPHYR_BASE": str(Path.home() / "zephyrproject" / "zephyr"),
        "PATH": "/usr/local/bin:/usr/bin:/bin",
    }

    # 初始化 west
    west_init = ["west", "init", "."]

    # 更新模块
    west_update = ["west", "update"]

    # 构建
    west_build = [
        "west",
        "build",
        "-p",
        "auto",
        "-b",
        board,
        str(project_dir),
        "-d",
        str(build_dir),
    ]

    print(f"Building Zephyr project for {board}...")
    try:
        subprocess.run(west_build, cwd=project_dir, check=True, env=env)
        print("Build successful!")

        # 返回 ELF 路径
        elf_path = build_dir / "zephyr" / "zephyr.elf"
        return elf_path
    except subprocess.CalledProcessError as e:
        print(f"Build failed: {e}")
        return None


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python build_zephyr.py <project_dir> [board]")
        sys.exit(1)

    project_dir = Path(sys.argv[1])
    board = sys.argv[2] if len(sys.argv) > 2 else "nucleo_f411re"

    build_zephyr(project_dir, board)
