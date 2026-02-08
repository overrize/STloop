"""CMake 构建模块"""
import logging
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional

log = logging.getLogger("stloop")


def _get_generator() -> str:
    """根据平台选择 CMake 生成器"""
    if sys.platform == "win32":
        if shutil.which("ninja"):
            return "Ninja"
        if shutil.which("make"):
            return "Unix Makefiles"
        # 尝试 Ninja 优先
        return "Ninja"
    return "Unix Makefiles"


def build(
    project_dir: Path,
    build_dir: Optional[Path] = None,
    cube_path: Optional[Path] = None,
    generator: Optional[str] = None,
) -> Path:
    """
    执行 CMake 配置与编译。
    返回生成的 .elf 路径。
    """
    project_dir = Path(project_dir).resolve()
    build_dir = build_dir or project_dir / "build"
    build_dir = Path(build_dir)
    build_dir.mkdir(parents=True, exist_ok=True)

    if cube_path is None:
        cube_path = project_dir / "cube" / "STM32CubeF4"
    cube_path = Path(cube_path).resolve()

    log.info("工程目录: %s", project_dir)
    log.info("构建目录: %s", build_dir)
    log.info("CUBE_ROOT: %s", cube_path)
    proj_ld = list(project_dir.glob("*.ld"))
    proj_startup = list(project_dir.glob("startup_stm32*.s"))
    log.info("工程目录下 .ld 数量: %d, startup_*.s 数量: %d", len(proj_ld), len(proj_startup))

    if not (cube_path / "Drivers").exists():
        raise FileNotFoundError(
            f"STM32Cube 未找到: {cube_path}\n"
            f"请确认 cube 路径正确，或运行: python -m stloop cube-download"
        )

    generator = generator or _get_generator()
    log.info("CMake 生成器: %s", generator)

    # CMake 配置
    cmake_cmd = [
        "cmake",
        "-G", generator,
        f"-DCUBE_ROOT={cube_path}",
        "-S", str(project_dir),
        "-B", str(build_dir),
    ]
    log.debug("执行: %s", " ".join(cmake_cmd))
    try:
        result = subprocess.run(
            cmake_cmd,
            capture_output=True,
            text=True,
            env=dict(**os.environ),
        )
        if result.returncode != 0:
            log.error("CMake 配置失败 (exit %d)", result.returncode)
            if result.stderr:
                log.error("stderr: %s", result.stderr)
            if result.stdout:
                log.error("stdout: %s", result.stdout)
            raise RuntimeError(
                f"CMake 配置失败:\n{result.stderr or result.stdout or '无输出'}"
            )
    except FileNotFoundError as e:
        raise RuntimeError(
            "未找到 cmake 命令，请安装 CMake 并加入 PATH。"
        ) from e

    # CMake 编译
    log.info("正在编译...")
    try:
        result = subprocess.run(
            ["cmake", "--build", str(build_dir)],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            log.error("编译失败 (exit %d)", result.returncode)
            if result.stderr:
                log.error("stderr: %s", result.stderr)
            if result.stdout:
                log.error("stdout: %s", result.stdout)
            err_msg = result.stderr or result.stdout or "无输出"
            raise RuntimeError(f"编译失败:\n{err_msg}")
    except FileNotFoundError:
        raise RuntimeError("未找到 cmake 命令") from None

    elf = build_dir / "stm32_app.elf"
    if not elf.exists():
        raise FileNotFoundError(f"编译未生成 {elf}，请检查 CMake 配置与 arm-none-eabi-gcc 是否已安装")

    log.info("编译成功: %s", elf)
    return elf
