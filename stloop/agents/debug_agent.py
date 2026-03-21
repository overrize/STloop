"""Debug Agent - 多通道调试监控

负责：
1. 串口数据监控和捕获
2. JTAG/SWD 调试接口管理
3. 逻辑分析仪数据捕获（如果可用）
4. 实时日志收集和分析
"""

import logging
import re
import subprocess
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from queue import Queue
from typing import Callable, Dict, List, Optional

log = logging.getLogger("stloop.debug_agent")


@dataclass
class DebugSession:
    """调试会话数据"""

    serial_logs: List[str] = field(default_factory=list)
    jtag_logs: List[str] = field(default_factory=list)
    logic_analyzer_data: Optional[str] = None
    start_time: float = field(default_factory=time.time)

    def get_summary(self) -> str:
        """获取日志摘要"""
        lines = []
        lines.append(f"调试会话 ({time.time() - self.start_time:.1f}s)")
        lines.append(f"  串口日志: {len(self.serial_logs)} 条")
        lines.append(f"  JTAG 日志: {len(self.jtag_logs)} 条")
        return "\n".join(lines)


class DebugAgent:
    """调试 Agent - 多通道监控"""

    def __init__(self):
        self.serial_port: Optional[str] = None
        self.baudrate: int = 115200
        self._serial_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._log_queue: Queue = Queue()
        self.current_session: Optional[DebugSession] = None

    def start_monitoring(
        self,
        serial_port: Optional[str] = None,
        auto_detect: bool = True,
    ) -> DebugSession:
        """开始监控

        Args:
            serial_port: 指定串口（如 COM3 或 /dev/ttyACM0）
            auto_detect: 是否自动检测串口

        Returns:
            DebugSession: 调试会话对象
        """
        self.current_session = DebugSession()

        # 自动检测串口
        if serial_port is None and auto_detect:
            serial_port = self._detect_serial_port()

        if serial_port:
            self.serial_port = serial_port
            self._start_serial_monitor()
            log.info(f"[Debug] 串口监控启动: {serial_port}")
        else:
            log.warning(f"[Debug] 未找到可用串口")

        return self.current_session

    def stop_monitoring(self) -> DebugSession:
        """停止监控并返回会话数据"""
        self._stop_event.set()

        if self._serial_thread and self._serial_thread.is_alive():
            self._serial_thread.join(timeout=2)

        log.info(f"[Debug] 监控停止")
        return self.current_session or DebugSession()

    def _detect_serial_port(self) -> Optional[str]:
        """自动检测串口"""
        import sys

        if sys.platform == "win32":
            # Windows: 使用 mode 命令检测
            try:
                result = subprocess.run(
                    ["mode"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                # 查找 COM 端口
                com_ports = re.findall(r"COM\d+", result.stdout)
                if com_ports:
                    return com_ports[0]
            except:
                pass
        else:
            # Linux/Mac: 查找 /dev/ttyACM* 或 /dev/ttyUSB*
            import glob

            ports = glob.glob("/dev/ttyACM*") + glob.glob("/dev/ttyUSB*")
            if ports:
                return ports[0]

        return None

    def _start_serial_monitor(self):
        """启动串口监控线程"""
        self._stop_event.clear()
        self._serial_thread = threading.Thread(
            target=self._serial_monitor_loop,
            daemon=True,
        )
        self._serial_thread.start()

    def _serial_monitor_loop(self):
        """串口监控循环"""
        try:
            import serial
        except ImportError:
            log.error(f"[Debug] pyserial 未安装，无法监控串口")
            return

        try:
            with serial.Serial(self.serial_port, self.baudrate, timeout=1) as ser:
                log.info(f"[Debug] 串口已连接: {self.serial_port}@{self.baudrate}")

                while not self._stop_event.is_set():
                    try:
                        line = ser.readline().decode("utf-8", errors="ignore").strip()
                        if line:
                            log.debug(f"[Serial] {line}")
                            if self.current_session:
                                self.current_session.serial_logs.append(line)
                    except Exception as e:
                        log.error(f"[Debug] 串口读取错误: {e}")
                        time.sleep(0.1)

        except Exception as e:
            log.error(f"[Debug] 串口连接失败: {e}")

    def get_recent_logs(self, count: int = 50) -> List[str]:
        """获取最近的日志"""
        if not self.current_session:
            return []
        return self.current_session.serial_logs[-count:]

    def capture_jtag_trace(self, duration: float = 5.0) -> List[str]:
        """捕获 JTAG/SWD 跟踪数据（需要 OpenOCD）"""
        logs = []

        # 这里简化处理，实际实现需要调用 OpenOCD
        log.info(f"[Debug] JTAG 跟踪捕获 {duration}s")

        return logs

    def analyze_behavior(self, expected: str) -> Dict[str, any]:
        """分析实际行为是否符合预期"""
        logs = self.get_recent_logs(100)
        log_text = "\n".join(logs)

        # 简单的关键词匹配分析
        analysis = {
            "logs_captured": len(logs),
            "time_span": self.current_session.start_time if self.current_session else 0,
            "patterns_found": [],
            "errors_found": [],
        }

        # 查找常见模式
        patterns = {
            "boot": r"boot|start|init",
            "gpio": r"gpio|pin|led",
            "uart": r"uart|serial|tx|rx",
            "error": r"error|fail|assert|panic",
        }

        for name, pattern in patterns.items():
            if re.search(pattern, log_text, re.IGNORECASE):
                analysis["patterns_found"].append(name)

        # 查找错误
        error_matches = re.findall(r"(error|fail|assert|panic).*", log_text, re.IGNORECASE)
        analysis["errors_found"] = error_matches[:10]  # 最多10个

        return analysis
