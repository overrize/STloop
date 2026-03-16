"""CMake 构建模块"""

import logging
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional

from .errors import BuildError, ConfigurationError

log = logging.getLogger("stloop")

# STLoop 仅支持 arm-none-eabi (GNU) 工具链，与 cube 的 gcc/ startup、.ld 对应
TOOLCHAIN_PREFIX = "arm-none-eabi"
TOOLCHAIN_HINT = (
    "请安装 arm-none-eabi-gcc 并加入 PATH。"
    "下载: https://developer.arm.com/downloads/-/arm-gnu-toolchain-downloads 或 xPack"
)


def _parse_build_error(stderr: str) -> str:
    """解析编译/CMake 错误，返回用户友好提示"""
    text = (stderr or "").strip()
    if not text:
        return "无错误输出"
    if "arm-none-eabi-gcc" in text and ("not found" in text or "No such file" in text):
        return f"未找到 {TOOLCHAIN_PREFIX}-gcc 编译器。\n{TOOLCHAIN_HINT}"
    if "CUBE_ROOT" in text or "STM32Cube" in text:
        return "STM32Cube 路径配置错误。\n请运行: python -m stloop cube-download"
    if "cmake" in text.lower() and ("not found" in text or "No such file" in text):
        return "未找到 cmake 命令，请安装 CMake 并加入 PATH。"
    # 返回截断的原始信息
    return text[:600] + ("..." if len(text) > 600 else "")


def ensure_toolchain() -> bool:
    """检测 arm-none-eabi-gcc 是否可用，不可用则抛异常。"""
    gcc = shutil.which(f"{TOOLCHAIN_PREFIX}-gcc")
    if not gcc:
        raise ConfigurationError(f"未找到 {TOOLCHAIN_PREFIX}-gcc 工具链。{TOOLCHAIN_HINT}")
    log.info("工具链: %s", gcc)
    return True


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

    # 检查是否有完整的 Cube 或内置的 CMSIS
    embedded_cmsis = project_dir / "cmsis_minimal"
    if not (cube_path / "Drivers").exists() and not embedded_cmsis.exists():
        raise ConfigurationError(
            f"STM32Cube 未找到: {cube_path}\n"
            f"请确认 cube 路径正确，或运行: python -m stloop cube-download"
        )

    # 如果有内置 CMSIS 但没有 Cube，使用内置 CMSIS
    if not (cube_path / "Drivers").exists() and embedded_cmsis.exists():
        log.info("使用内置 CMSIS，无需外部 Cube")
        # cube_path 在这里不会被 CMake 使用，因为 CMakeLists.txt 会检测 cmsis_minimal

    ensure_toolchain()
    generator = generator or _get_generator()
    log.info("CMake 生成器: %s", generator)

    # CMake 配置 - 使用工具链文件强制 ARM 交叉编译
    cmake_toolchain = project_dir / "cmake" / "arm-gcc-toolchain.cmake"
    cmake_cmd = [
        "cmake",
        "-G",
        generator,
        f"-DCMAKE_TOOLCHAIN_FILE={cmake_toolchain}",
        f"-DCUBE_ROOT={cube_path}",
        "-S",
        str(project_dir),
        "-B",
        str(build_dir),
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
            err_text = result.stderr or result.stdout or "无输出"

            # 检查是否是生成器不匹配错误
            if "generator" in err_text.lower() and "does not match" in err_text.lower():
                log.warning("检测到 CMake 生成器不匹配，清理缓存并重新配置...")
                import shutil

                cache_file = build_dir / "CMakeCache.txt"
                files_dir = build_dir / "CMakeFiles"
                if cache_file.exists():
                    cache_file.unlink()
                    log.debug("删除: %s", cache_file)
                if files_dir.exists():
                    shutil.rmtree(files_dir)
                    log.debug("删除: %s", files_dir)

                # 重新尝试配置
                result = subprocess.run(
                    cmake_cmd,
                    capture_output=True,
                    text=True,
                    env=dict(**os.environ),
                )
                if result.returncode == 0:
                    log.info("重新配置成功")
                else:
                    err_text = result.stderr or result.stdout or "无输出"
                    log.error("CMake 重新配置失败")
                    if result.stderr:
                        log.error("stderr: %s", result.stderr)
                    if result.stdout:
                        log.error("stdout: %s", result.stdout)
                    msg = _parse_build_error(err_text)
                    raise BuildError(f"CMake 配置失败:\n{msg}")
            else:
                log.error("CMake 配置失败 (exit %d)", result.returncode)
                if result.stderr:
                    log.error("stderr: %s", result.stderr)
                if result.stdout:
                    log.error("stdout: %s", result.stdout)
                msg = _parse_build_error(err_text)
                raise BuildError(f"CMake 配置失败:\n{msg}")
    except FileNotFoundError as e:
        raise ConfigurationError("未找到 cmake 命令，请安装 CMake 并加入 PATH。") from e

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
            err_text = result.stderr or result.stdout or "无输出"
            if result.stderr:
                log.error("stderr: %s", result.stderr)
            if result.stdout:
                log.error("stdout: %s", result.stdout)
            msg = _parse_build_error(err_text)
            raise BuildError(f"编译失败:\n{msg}")
    except FileNotFoundError:
        raise ConfigurationError("未找到 cmake 命令") from None

    elf = build_dir / "stm32_app.elf"
    if not elf.exists():
        raise BuildError(f"编译未生成 {elf}，请检查 CMake 配置与 arm-none-eabi-gcc 是否已安装")

    log.info("编译成功: %s", elf)
    return elf
