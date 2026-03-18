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


def _is_zephyr_project(project_dir: Path) -> bool:
    """检查是否为 Zephyr 项目"""
    return (project_dir / "prj.conf").exists() and "zephyr" in (
        project_dir / "CMakeLists.txt"
    ).read_text(encoding="utf-8", errors="ignore").lower()


def check_zephyr_environment() -> tuple[bool, str]:
    """检查 Zephyr 环境是否就绪

    Returns:
        (is_ready, message): 是否就绪及状态信息
    """
    # 检查 west 工具
    west = shutil.which("west")
    if not west:
        return False, "未找到 west 工具"

    # 检查 ZEPHYR_BASE
    zephyr_base = os.environ.get("ZEPHYR_BASE")
    if not zephyr_base:
        # 尝试常见路径
        for path in [
            Path.home() / "zephyrproject" / "zephyr",
            Path("/opt/zephyrproject/zephyr"),
            Path("C:/zephyrproject/zephyr"),
        ]:
            if path.exists():
                zephyr_base = str(path)
                os.environ["ZEPHYR_BASE"] = zephyr_base
                break

    if not zephyr_base or not Path(zephyr_base).exists():
        return False, "未找到 Zephyr SDK (ZEPHYR_BASE)"

    return True, f"ZEPHYR_BASE: {zephyr_base}"


def _build_zephyr(
    project_dir: Path, build_dir: Path, board: str = "nucleo_f411re", use_zephyr: bool = True
) -> Path:
    """使用 west 构建 Zephyr 项目，或在无 Zephyr 环境时回退到标准 CMake

    Args:
        project_dir: 项目目录
        build_dir: 构建目录
        board: 目标板
        use_zephyr: 是否使用 Zephyr（如果为 False 则直接使用标准 CMake）
    """
    if not use_zephyr:
        log.info("使用标准 CMSIS 构建（跳过 Zephyr）...")
        return _build_cmake(project_dir, build_dir, board)

    log.info("检测到 Zephyr 项目，尝试使用 west 构建...")

    # 检查 Zephyr 环境
    is_ready, msg = check_zephyr_environment()
    if not is_ready:
        log.info(f"{msg}，回退到标准 CMSIS 构建...")
        return _build_cmake(project_dir, build_dir, board)

    zephyr_base = os.environ.get("ZEPHYR_BASE")
    west = shutil.which("west")
    log.info("ZEPHYR_BASE: %s", zephyr_base)
    log.info("目标板: %s", board)

    # 构建命令
    west_cmd = [west, "build", "-p", "auto", "-b", board, str(project_dir), "-d", str(build_dir)]

    log.debug("执行: %s", " ".join(west_cmd))
    try:
        result = subprocess.run(
            west_cmd,
            capture_output=True,
            text=True,
            env=dict(**os.environ),
        )
        if result.returncode != 0:
            raise BuildError(f"Zephyr 构建失败:\n{result.stderr or result.stdout}")

        # 查找生成的 ELF
        elf_paths = [
            build_dir / "zephyr" / "zephyr.elf",
            build_dir / "zephyr.elf",
        ]
        for elf_path in elf_paths:
            if elf_path.exists():
                log.info("[OK] Zephyr 构建成功: %s", elf_path)
                return elf_path

        raise BuildError("构建成功但未找到 ELF 文件")

    except subprocess.CalledProcessError as e:
        raise BuildError(f"Zephyr 构建失败: {e}")


def _build_cmake(project_dir: Path, build_dir: Path, board: str = "nucleo_f411re") -> Path:
    """使用标准 CMake 构建 Zephyr 兼容项目（回退方案）"""
    log.info("使用标准 CMake 构建 Zephyr 兼容项目...")
    log.info("目标板: %s", board)

    ensure_toolchain()
    generator = _get_generator()
    log.info("CMake 生成器: %s", generator)

    # CMake 配置
    cmake_cmd = [
        "cmake",
        "-G",
        generator,
        f"-DBOARD={board}",
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
            err_text = _parse_build_error(result.stderr or result.stdout)
            raise BuildError(f"CMake 配置失败:\n{err_text}")

        # 编译
        build_cmd = ["cmake", "--build", str(build_dir)]
        log.info("正在编译...")

        result = subprocess.run(
            build_cmd,
            capture_output=True,
            text=True,
            env=dict(**os.environ),
        )
        if result.returncode != 0:
            err_text = _parse_build_error(result.stderr or result.stdout)
            raise BuildError(f"编译失败:\n{err_text}")

        # 查找生成的 ELF (Windows 上可能是 .elf.exe)
        elf_patterns = [
            "zephyr.elf*",
            "stloop_zephyr_compat.elf*",
            "stm32_app.elf*",
            "*.elf*",
        ]
        for pattern in elf_patterns:
            matches = list(build_dir.glob(pattern))
            if matches:
                elf_path = matches[0]
                log.info("[OK] 构建成功: %s", elf_path)
                return elf_path

        raise BuildError("构建成功但未找到 ELF 文件")

    except subprocess.CalledProcessError as e:
        raise BuildError(f"CMake 构建失败: {e}")


def build(
    project_dir: Path,
    build_dir: Optional[Path] = None,
    cube_path: Optional[Path] = None,
    generator: Optional[str] = None,
    board: Optional[str] = None,
    use_zephyr: Optional[bool] = None,
) -> Path:
    """
    执行 CMake 配置与编译。
    返回生成的 .elf 路径。

    Args:
        project_dir: 项目目录
        build_dir: 构建目录（默认项目目录下的 build）
        cube_path: STM32Cube 路径
        generator: CMake 生成器
        board: 目标板（用于 Zephyr）
        use_zephyr: 是否使用 Zephyr（None=自动询问，True=使用，False=不使用）
    """
    project_dir = Path(project_dir).resolve()
    build_dir = build_dir or project_dir / "build"
    build_dir = Path(build_dir)
    build_dir.mkdir(parents=True, exist_ok=True)

    # 检查是否为 Zephyr 项目
    if _is_zephyr_project(project_dir):
        return _build_zephyr(project_dir, build_dir, board or "nucleo_f411re", use_zephyr or False)

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
