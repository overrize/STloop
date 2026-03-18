"""下载 STM32CubeF4 软件包"""

import logging
import shutil
import subprocess
import sys
import time
from pathlib import Path

log = logging.getLogger("stloop")

CUBE_VERSION = "1.28.0"
CUBE_GIT_URL = "https://github.com/STMicroelectronics/STM32CubeF4.git"
MAX_RETRIES = 3
RETRY_DELAY = 2

DOWNLOAD_FAIL_HINT = """
若自动下载反复失败，可手动 clone 后放到 cube/STM32CubeF4：
  git clone --recursive --depth 1 --branch v1.28.0 \
    https://github.com/STMicroelectronics/STM32CubeF4.git \
    cube/STM32CubeF4
  
  或使用镜像（国内）：
  git clone --recursive --depth 1 --branch v1.28.0 \
    https://gitee.com/mirrors/STM32CubeF4.git \
    cube/STM32CubeF4
"""


def _find_existing_cube(target_dir: Path) -> Path | None:
    """下载前确认：若 cube 文件夹已有芯片库（含 Drivers/CMSIS/Device），返回路径，否则 None"""
    target_dir = Path(target_dir).resolve()

    def _scan(cube_dir: Path) -> Path | None:
        if not cube_dir.exists():
            return None
        # 检查是否包含完整的 CMSIS Device（关键的 system_stm32f4xx.c）
        cmsis_device = (
            cube_dir / "STM32CubeF4" / "Drivers" / "CMSIS" / "Device" / "ST" / "STM32F4xx"
        )
        if cmsis_device.exists() and any(cmsis_device.iterdir()):
            return cube_dir / "STM32CubeF4"
        # 回退：仅检查 Drivers 存在
        if (cube_dir / "STM32CubeF4" / "Drivers").exists():
            return cube_dir / "STM32CubeF4"
        for d in cube_dir.iterdir():
            if d.is_dir() and "STM32CubeF4" in d.name:
                cmsis_device = d / "Drivers" / "CMSIS" / "Device" / "ST" / "STM32F4xx"
                if cmsis_device.exists() and any(cmsis_device.iterdir()):
                    return d
                if (d / "Drivers").exists():
                    return d
        return None

    if (target_dir / "Drivers" / "CMSIS" / "Device" / "ST" / "STM32F4xx").exists():
        return target_dir
    if (target_dir / "Drivers").exists():
        return target_dir
    # 1) work_dir/cube
    found = _scan(target_dir.parent)
    if found:
        return found
    # 2) work_dir 上一级的 cube（STloop 与 cube 同级时，如 STLOOP_TEST/cube 与 STLOOP_TEST/STloop）
    parent_cube = target_dir.parent.parent.parent / "cube"
    return _scan(parent_cube)


def _clone_cube_with_git(target_dir: Path, use_mirror: bool = False) -> None:
    """使用 git clone --recursive 下载 cube（包含 submodule）"""
    url = CUBE_GIT_URL
    if use_mirror:
        url = "https://gitee.com/mirrors/STM32CubeF4.git"

    cmd = [
        "git",
        "clone",
        "--recursive",  # 关键：下载子模块
        "--depth",
        "1",  # 仅下载最新版本，节省时间和空间
        "--branch",
        f"v{CUBE_VERSION}",
        url,
        str(target_dir),
    ]

    log.info("执行: %s", " ".join(cmd))
    print(f"正在克隆 STM32CubeF4 v{CUBE_VERSION}...")
    print(f"  源: {url}")

    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")

    if result.returncode != 0:
        raise RuntimeError(f"Git clone 失败: {result.stderr}")

    print(f"  ✓ 克隆完成")


def download_cube(target_dir: Path, raise_on_fail: bool = True) -> Path:
    """
    下载 STM32CubeF4 到 target_dir（使用 git clone --recursive 确保包含 submodule）
    raise_on_fail: True 时抛异常，False 时 sys.exit(1)
    """
    target_dir = Path(target_dir).resolve()
    log.info("检查 STM32CubeF4: %s", target_dir)

    existing = _find_existing_cube(target_dir)
    if existing is not None:
        log.info("cube 目录已有芯片库，跳过下载: %s", existing)
        return existing

    target_dir.parent.mkdir(parents=True, exist_ok=True)

    last_error = None
    for attempt in range(1, MAX_RETRIES + 1):
        log.info("下载尝试 %d/%d", attempt, MAX_RETRIES)
        print(f"正在获取 STM32CubeF4 v{CUBE_VERSION}... (尝试 {attempt}/{MAX_RETRIES})")

        try:
            # 清理可能存在的残留目录
            if target_dir.exists():
                print(f"  清理残留目录...")
                shutil.rmtree(target_dir)

            # 尝试使用官方源
            use_mirror = attempt > 1  # 第二次尝试使用镜像
            _clone_cube_with_git(target_dir, use_mirror=use_mirror)
            last_error = None
            break

        except Exception as e:
            last_error = e
            log.warning("下载失败 (尝试 %d/%d): %s", attempt, MAX_RETRIES, e)
            print(f"\n  ✗ 失败: {e}")
            if target_dir.exists():
                shutil.rmtree(target_dir, ignore_errors=True)
            if attempt < MAX_RETRIES:
                print(f"  {RETRY_DELAY} 秒后重试...")
                time.sleep(RETRY_DELAY)

    if last_error is not None:
        print(DOWNLOAD_FAIL_HINT, file=sys.stderr)
        if raise_on_fail:
            raise RuntimeError(f"STM32CubeF4 下载失败: {last_error}") from last_error
        sys.exit(1)

    # 验证关键文件是否存在
    cmsis_device_dir = target_dir / "Drivers" / "CMSIS" / "Device" / "ST" / "STM32F4xx"
    if not cmsis_device_dir.exists() or not any(cmsis_device_dir.iterdir()):
        msg = "下载完成但 CMSIS Device 目录为空，可能 submodule 未正确下载"
        log.error(msg)
        print(f"\n  ✗ {msg}", file=sys.stderr)
        print("  请检查网络连接或手动下载", file=sys.stderr)
        print(DOWNLOAD_FAIL_HINT, file=sys.stderr)
        if raise_on_fail:
            raise RuntimeError(msg)
        sys.exit(1)

    # 验证关键文件
    key_files = [
        target_dir
        / "Drivers"
        / "CMSIS"
        / "Device"
        / "ST"
        / "STM32F4xx"
        / "Include"
        / "stm32f4xx.h",
        target_dir
        / "Drivers"
        / "CMSIS"
        / "Device"
        / "ST"
        / "STM32F4xx"
        / "Source"
        / "Templates"
        / "system_stm32f4xx.c",
    ]

    missing = [f for f in key_files if not f.exists()]
    if missing:
        msg = f"关键文件缺失: {[f.name for f in missing]}"
        log.error(msg)
        print(f"\n  ✗ {msg}", file=sys.stderr)
        if raise_on_fail:
            raise RuntimeError(msg)
        sys.exit(1)

    log.info("STM32CubeF4 就绪: %s", target_dir)
    print(f"  ✓ STM32CubeF4 就绪: {target_dir}")
    return target_dir


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format="[%(name)s] %(levelname)s: %(message)s")
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd() / "cube" / "STM32CubeF4"
    try:
        download_cube(out, raise_on_fail=False)
    except RuntimeError:
        sys.exit(1)
