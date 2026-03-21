"""
Renode 仿真器集成

加载裸机 ELF 在 Renode 中运行，用于无硬件验证：
gen → build → sim，无需 pyOCD 与实体硬件

增强功能：
- 自动生成 .resc 脚本
- 支持 UART 监控
- GDB 调试接口
- STM32 平台映射
"""

import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional, Dict, List
from dataclasses import dataclass
from enum import Enum

# 可选：通过环境变量指定 renode 可执行路径
RENODE_ENV = "RENODE_BIN"


class RenodeStatus(Enum):
    """Renode 状态"""

    NOT_INSTALLED = "not_installed"
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    ERROR = "error"


@dataclass
class RenodeConfig:
    """Renode 配置"""

    mcu: str = "STM32F411RE"
    gdb_port: int = 3333
    telnet_port: int = 1234
    pause_on_startup: bool = False
    show_gui: bool = True
    enable_uart: bool = True


def find_renode_bin() -> Optional[Path]:
    """查找 renode 可执行文件：优先 RENODE_BIN，否则 PATH 中的 renode。"""
    import shutil

    env_bin = os.environ.get(RENODE_ENV)
    if env_bin:
        p = Path(env_bin)
        if p.is_file():
            return p
        if p.is_dir() and (p / "Renode.exe").is_file():
            return p / "Renode.exe"
    ren = shutil.which("renode") or shutil.which("Renode")
    if ren:
        return Path(ren)
    return None


# STM32 到 Renode 平台的映射
# 注意：使用 Renode 实际存在的平台文件
PLATFORM_MAP: Dict[str, str] = {
    # STM32F4 系列 - 使用通用的 stm32f4.repl
    "STM32F411RE": "platforms/cpus/stm32f4.repl",
    "STM32F407VG": "platforms/cpus/stm32f4.repl",
    "STM32F405RG": "platforms/cpus/stm32f4.repl",
    "STM32F446RE": "platforms/cpus/stm32f4.repl",
    # 开发板
    "NUCLEO_F411RE": "platforms/boards/nucleo_f411re.repl",
    "STM32F4_DISCOVERY": "platforms/boards/stm32f4_discovery.repl",
}


def get_platform_file(mcu: str) -> Optional[str]:
    """
    获取 MCU 对应的 Renode 平台文件

    Args:
        mcu: MCU 型号（如 STM32F411RE）

    Returns:
        平台文件路径，如果不支持则返回 None
    """
    # 直接匹配
    if mcu.upper() in PLATFORM_MAP:
        return PLATFORM_MAP[mcu.upper()]

    # 尝试部分匹配
    mcu_upper = mcu.upper()
    for key, value in PLATFORM_MAP.items():
        if mcu_upper in key or key in mcu_upper:
            return value

    return None


def _get_renode_platforms_dir() -> Optional[Path]:
    """获取 Renode platforms 目录"""
    bin_path = find_renode_bin()
    if not bin_path:
        return None
    platforms_dir = bin_path.parent.parent / "platforms"
    if platforms_dir.exists():
        return platforms_dir
    if sys.platform == "win32":
        bin_str = str(bin_path)
        if len(bin_str) > 2 and bin_str[0] == "/" and bin_str[2] == "/":
            drive = bin_str[1].upper() + ":"
            windows_path = Path(drive + bin_str[2:])
            platforms_dir = windows_path.parent.parent / "platforms"
            if platforms_dir.exists():
                return platforms_dir
    return None


def generate_resc_script(
    elf_path: Path,
    mcu: str = "STM32F411RE",
    config: Optional[RenodeConfig] = None,
    output_path: Optional[Path] = None,
) -> Path:
    """
    生成 Renode 脚本 (.resc)

    Args:
        elf_path: 固件 ELF 文件路径
        mcu: MCU 型号
        config: Renode 配置
        output_path: 输出路径，默认使用 firmware 所在目录

    Returns:
        生成的 .resc 文件路径
    """
    config = config or RenodeConfig(mcu=mcu)

    if output_path is None:
        output_path = elf_path.parent / "simulation.resc"

    platform = get_platform_file(mcu) or "platforms/cpus/stm32f4.repl"

    platforms_dir = _get_renode_platforms_dir()
    if platforms_dir:
        platform_file = platforms_dir / platform.replace("platforms/", "").replace("/", os.sep)
        if platform_file.exists():
            platform = str(platform_file).replace("\\", "/")

    elf_abs_path = Path(elf_path).resolve()
    elf_path_str = str(elf_abs_path).replace("\\", "/")

    # 生成脚本内容 - 使用正确的 Renode 语法
    script_lines = [
        f"; Renode Simulation Script for {mcu}",
        f"; Firmware: {elf_path.name}",
        "",
        "; Create machine",
        f'mach create "{mcu}"',
        "",
        "; Load platform description",
        f"machine LoadPlatformDescription @{platform}",
        "",
        "; Load firmware",
        f'sysbus LoadELF "{elf_path_str}"',
    ]

    if config.enable_uart:
        import tempfile

        uart_path = tempfile.gettempdir().replace("\\", "/") + "/renode_uart"
        script_lines.extend(
            [
                "",
                "; Setup UART",
                f'emulation CreateUartPtyTerminal "term" "{uart_path}"',
                "connector Connect sysbus.usart1 term",
            ]
        )

    # 添加 GDB 服务器支持（如果有配置）
    if hasattr(config, "gdb_port") and config.gdb_port:
        script_lines.extend(
            [
                "",
                f"; Start GDB server on port {config.gdb_port}",
                f"machine StartGdbServer {config.gdb_port}",
            ]
        )

    # 启动或暂停
    script_lines.extend(
        [
            "",
            "; Start simulation",
            "start",
        ]
    )

    output_path.write_text("\n".join(script_lines), encoding="utf-8")
    return output_path


def run(
    elf_path: Path,
    repl_path: Optional[Path] = None,
    timeout_sec: Optional[int] = None,
    mcu: str = "STM32F411RE",
    headless: bool = True,
) -> subprocess.CompletedProcess:
    """Run ELF in Renode simulator."""
    elf_path = Path(elf_path).resolve()
    if not elf_path.is_file():
        raise FileNotFoundError(f"ELF not found: {elf_path}")

    bin_path = find_renode_bin()
    if not bin_path:
        raise RuntimeError(
            "Renode not found. Please install Renode and add to PATH, "
            "or set RENODE_BIN environment variable. "
            "See https://renode.io/"
        )

    resc_script = generate_resc_script(elf_path, mcu=mcu)

    cmd = [str(bin_path), str(resc_script)]

    if headless:
        cmd.extend(["--disable-xwt", "--port", "0"])
    else:
        cmd.append("--console")

    timeout = (timeout_sec + 10) if timeout_sec else 60
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=timeout,
        cwd=elf_path.parent,
    )


class RenodeSimulator:
    """
    Renode 仿真器类

    提供高级仿真功能，支持交互式控制和监控。
    """

    def __init__(self):
        self.process: Optional[subprocess.Popen] = None
        self.status = RenodeStatus.STOPPED
        self.config: Optional[RenodeConfig] = None
        self._bin_path = find_renode_bin()

    def is_installed(self) -> bool:
        """检查 Renode 是否已安装"""
        return self._bin_path is not None

    def start(
        self,
        elf_path: Path,
        mcu: str = "STM32F411RE",
        config: Optional[RenodeConfig] = None,
        blocking: bool = False,
        timeout: Optional[int] = None,
    ) -> bool:
        """
        启动 Renode 仿真

        Args:
            elf_path: 固件 ELF 路径
            mcu: MCU 型号
            config: 配置
            blocking: 是否阻塞等待
            timeout: 超时时间（秒）

        Returns:
            是否成功启动
        """
        if not self.is_installed():
            return False

        if self.process is not None:
            return False

        self.config = config or RenodeConfig(mcu=mcu)

        # 生成脚本
        resc_script = generate_resc_script(elf_path, mcu, self.config)

        # 构建命令
        cmd = [
            str(self._bin_path),
            str(resc_script),
        ]

        if not self.config.show_gui:
            cmd.append("--disable-gui")

        if blocking:
            # 阻塞模式
            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                )
                return result.returncode == 0
            except subprocess.TimeoutExpired:
                return False
        else:
            # 非阻塞模式 - 使用交互式终端连接
            self.process = subprocess.Popen(
                cmd,
                stdin=None,  # 继承父进程 stdin，允许用户交互
                stdout=None,  # 继承父进程 stdout，直接显示输出
                stderr=None,  # 继承父进程 stderr
            )
            self.status = RenodeStatus.RUNNING
            return True

    def stop(self) -> bool:
        """停止仿真"""
        if self.process is None:
            return True

        try:
            self.process.terminate()
            self.process.wait(timeout=5)
            self.status = RenodeStatus.STOPPED
            return True
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.status = RenodeStatus.STOPPED
            return True
        except Exception:
            return False

    def is_running(self) -> bool:
        """检查是否在运行"""
        if self.process is None:
            return False
        return self.process.poll() is None


def list_supported_platforms() -> List[Dict[str, str]]:
    """列出支持的 STM32 平台"""
    platforms = []

    for mcu, platform_file in PLATFORM_MAP.items():
        platforms.append(
            {
                "mcu": mcu,
                "platform": platform_file,
                "type": "Board" if "boards" in platform_file else "CPU",
            }
        )

    return platforms
