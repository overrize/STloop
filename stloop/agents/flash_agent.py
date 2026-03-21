"""Flash Agent - 自动烧录与连接管理

负责：
1. 检测开发板连接
2. 自动烧录（支持多种工具）
3. 烧录失败重试
4. 切换烧录工具（west → pyocd → openocd）
5. 检测连接问题并提示
"""

import logging
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional
import shutil

log = logging.getLogger("stloop.flash_agent")


@dataclass
class FlashResult:
    """烧录结果"""

    success: bool
    output: str = ""
    error: str = ""
    tool_used: str = ""
    retries: int = 0


class FlashAgent:
    """烧录 Agent - 自动烧录与错误恢复"""

    # 支持的烧录工具及其优先级
    FLASH_TOOLS = ["west", "pyocd", "openocd"]

    def __init__(self, max_retries: int = 3, retry_delay: float = 2.0):
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    def flash_with_retry(
        self,
        elf_path: Path,
        board: str,
        timeout: int = 60,
    ) -> FlashResult:
        """烧录 ELF 文件，失败时重试和切换工具

        Args:
            elf_path: ELF 文件路径
            board: 目标板
            timeout: 超时时间（秒）

        Returns:
            FlashResult: 烧录结果
        """
        log.info(f"[Flash] 开始烧录: {elf_path}")

        # 首先检查开发板连接
        if not self._check_board_connection():
            log.error(f"[Flash] 未检测到开发板连接")
            return FlashResult(
                success=False,
                error="未检测到开发板连接。请检查:\n"
                "1. USB 线是否连接正确\n"
                "2. 开发板电源是否开启\n"
                "3. 驱动是否安装（Windows）",
            )

        # 尝试不同工具
        for tool in self.FLASH_TOOLS:
            if not self._check_tool_available(tool):
                log.debug(f"[Flash] 工具不可用: {tool}")
                continue

            log.info(f"[Flash] 使用工具: {tool}")

            for retry in range(self.max_retries):
                if retry > 0:
                    log.info(f"[Flash] 重试 {retry}/{self.max_retries}...")
                    time.sleep(self.retry_delay)

                result = self._flash_with_tool(elf_path, board, tool, timeout)
                result.retries = retry
                result.tool_used = tool

                if result.success:
                    log.info(f"[Flash] ✓ 烧录成功")
                    return result

                log.warning(f"[Flash] ✗ 失败: {result.error[:100]}")

                # 检查是否可恢复的错误
                if not self._is_recoverable_error(result.error):
                    log.error(f"[Flash] 不可恢复的错误，切换工具")
                    break

        # 所有工具都失败
        return FlashResult(
            success=False,
            error=f"所有烧录工具均失败。已尝试: {', '.join(self.FLASH_TOOLS)}",
            retries=self.max_retries,
        )

    def _check_board_connection(self) -> bool:
        """检查开发板是否连接"""
        # 方法1: 检查 USB 设备（通过 pyocd 或 lsusb）
        if shutil.which("pyocd"):
            try:
                result = subprocess.run(
                    ["pyocd", "list"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if "No available debug probes" not in result.stdout:
                    log.debug(f"[Flash] pyocd 检测到设备")
                    return True
            except:
                pass

        # 方法2: 检查串口设备
        import sys

        if sys.platform == "win32":
            try:
                result = subprocess.run(
                    ["mode"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if "COM" in result.stdout:
                    log.debug(f"[Flash] 检测到串口设备")
                    return True
            except:
                pass
        else:
            # Linux/Mac: 检查 /dev/ttyACM* 或 /dev/ttyUSB*
            import glob

            if glob.glob("/dev/ttyACM*") or glob.glob("/dev/ttyUSB*"):
                log.debug(f"[Flash] 检测到串口设备")
                return True

        # 方法3: 尝试执行 west flash --runner list
        if shutil.which("west"):
            try:
                result = subprocess.run(
                    ["west", "flash", "--runner", "list"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if result.returncode == 0:
                    log.debug(f"[Flash] west 可用")
                    return True
            except:
                pass

        log.warning(f"[Flash] 未检测到开发板")
        return False

    def _check_tool_available(self, tool: str) -> bool:
        """检查工具是否可用"""
        return shutil.which(tool) is not None

    def _flash_with_tool(
        self,
        elf_path: Path,
        board: str,
        tool: str,
        timeout: int,
    ) -> FlashResult:
        """使用指定工具烧录"""

        if tool == "west":
            return self._flash_with_west(elf_path, board, timeout)
        elif tool == "pyocd":
            return self._flash_with_pyocd(elf_path, timeout)
        elif tool == "openocd":
            return self._flash_with_openocd(elf_path, board, timeout)
        else:
            return FlashResult(
                success=False,
                error=f"未知工具: {tool}",
            )

    def _flash_with_west(
        self,
        elf_path: Path,
        board: str,
        timeout: int,
    ) -> FlashResult:
        """使用 west flash 烧录"""
        build_dir = elf_path.parent.parent  # zephyr.elf -> build/zephyr/

        cmd = ["west", "flash", "-d", str(build_dir)]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
            )

            output = result.stdout + "\n" + result.stderr

            if result.returncode == 0:
                return FlashResult(success=True, output=output)
            else:
                return FlashResult(
                    success=False,
                    output=output,
                    error=f"west flash 失败: {output[-500:]}",
                )

        except subprocess.TimeoutExpired:
            return FlashResult(
                success=False,
                error=f"west flash 超时 ({timeout}s)",
            )
        except Exception as e:
            return FlashResult(
                success=False,
                error=f"west flash 异常: {e}",
            )

    def _flash_with_pyocd(
        self,
        elf_path: Path,
        timeout: int,
    ) -> FlashResult:
        """使用 pyocd 烧录"""
        cmd = ["pyocd", "flash", "-t", "stm32f411re", str(elf_path)]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
            )

            output = result.stdout + "\n" + result.stderr

            if result.returncode == 0:
                return FlashResult(success=True, output=output)
            else:
                return FlashResult(
                    success=False,
                    output=output,
                    error=f"pyocd 失败: {output[-500:]}",
                )

        except subprocess.TimeoutExpired:
            return FlashResult(
                success=False,
                error=f"pyocd 超时 ({timeout}s)",
            )
        except Exception as e:
            return FlashResult(
                success=False,
                error=f"pyocd 异常: {e}",
            )

    def _flash_with_openocd(
        self,
        elf_path: Path,
        board: str,
        timeout: int,
    ) -> FlashResult:
        """使用 openocd 烧录"""
        # 简化版，实际使用需要更复杂的配置
        cmd = [
            "openocd",
            "-f",
            "interface/stlink.cfg",
            "-f",
            "target/stm32f4x.cfg",
            "-c",
            f"program {elf_path} verify reset exit",
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
            )

            output = result.stdout + "\n" + result.stderr

            if result.returncode == 0:
                return FlashResult(success=True, output=output)
            else:
                return FlashResult(
                    success=False,
                    output=output,
                    error=f"openocd 失败: {output[-500:]}",
                )

        except subprocess.TimeoutExpired:
            return FlashResult(
                success=False,
                error=f"openocd 超时 ({timeout}s)",
            )
        except Exception as e:
            return FlashResult(
                success=False,
                error=f"openocd 异常: {e}",
            )

    def _is_recoverable_error(self, error: str) -> bool:
        """判断错误是否可恢复（适合重试）"""
        recoverable_patterns = [
            "connection refused",
            "device not found",
            "target not halted",
            "timeout",
            "busy",
            "access port",
        ]

        error_lower = error.lower()
        return any(pattern in error_lower for pattern in recoverable_patterns)
