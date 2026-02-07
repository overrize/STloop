"""CMake 构建模块"""
import os
import subprocess
from pathlib import Path
from typing import Optional


def build(
    project_dir: Path,
    build_dir: Optional[Path] = None,
    cube_path: Optional[Path] = None,
    generator: str = "Unix Makefiles",
) -> Path:
    """
    执行 CMake 配置与编译。
    返回生成的 .elf 路径。
    """
    project_dir = Path(project_dir)
    build_dir = build_dir or project_dir / "build"
    build_dir.mkdir(parents=True, exist_ok=True)

    # 若未指定 cube_path，使用 project_dir/cube
    if cube_path is None:
        cube_path = project_dir / "cube" / "STM32CubeF4"
    cube_path = Path(cube_path)
    if not (cube_path / "Drivers").exists():
        raise FileNotFoundError(
            f"STM32Cube 未找到: {cube_path}\n"
            "请运行: python scripts/download_cube.py"
        )

    env = dict(**os.environ)
    env["CUBE_ROOT"] = str(cube_path)

    # Configure
    subprocess.run(
        [
            "cmake",
            "-G", generator,
            f"-DCUBE_ROOT={cube_path}",
            "-S", str(project_dir),
            "-B", str(build_dir),
        ],
        check=True,
        env=env,
    )

    # Build（跨平台使用 cmake --build）
    subprocess.run(["cmake", "--build", str(build_dir)], check=True)

    elf = build_dir / "stm32_app.elf"
    if not elf.exists():
        raise FileNotFoundError(f"编译未生成 {elf}")
    return elf
