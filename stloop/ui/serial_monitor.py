"""
Serial Monitor - 串口监控器

Embedder 风格的实时串口数据显示界面。
支持：
- 文本和十六进制模式
- 日志级别自动识别
- 时间戳
- 滚动历史
"""

import threading
import time
from collections import deque
from datetime import datetime
from typing import Optional, Callable, List
from enum import Enum
from dataclasses import dataclass

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.live import Live
from rich.layout import Layout
from rich.table import Table
from rich import box

try:
    import serial
    import serial.tools.list_ports

    HAS_SERIAL = True
except ImportError:
    HAS_SERIAL = False
    serial = None

from stloop.ui.console import get_console


class DisplayMode(str, Enum):
    """显示模式"""

    TEXT = "text"
    HEX = "hex"
    MIXED = "mixed"


class LogLevel(str, Enum):
    """日志级别"""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"
    UNKNOWN = "UNKNOWN"


@dataclass
class SerialMessage:
    """串口消息"""

    timestamp: datetime
    data: bytes
    level: LogLevel = LogLevel.UNKNOWN

    def get_text(self) -> str:
        """获取文本表示"""
        try:
            return self.data.decode("utf-8", errors="replace").rstrip()
        except:
            return self.data.hex()

    def get_hex(self) -> str:
        """获取十六进制表示"""
        return " ".join(f"{b:02x}" for b in self.data)


class SerialMonitor:
    """
    串口监控器

    提供实时串口数据显示，支持：
    - 多视图模式（文本/十六进制/混合）
    - 自动日志级别识别
    - 连接状态监控
    - 历史记录滚动
    """

    # 日志级别识别关键词
    LEVEL_PATTERNS = {
        LogLevel.DEBUG: ["[DEBUG]", "DBG", "debug:"],
        LogLevel.INFO: ["[INFO]", "INF", "info:"],
        LogLevel.WARNING: ["[WARN]", "[WARNING]", "WRN", "warn:"],
        LogLevel.ERROR: ["[ERROR]", "[ERR]", "ERR", "error:"],
        LogLevel.CRITICAL: ["[CRITICAL]", "[FATAL]", "CRIT", "fatal:"],
    }

    # 样式映射
    LEVEL_STYLES = {
        LogLevel.DEBUG: "dim",
        LogLevel.INFO: "blue",
        LogLevel.WARNING: "yellow",
        LogLevel.ERROR: "red",
        LogLevel.CRITICAL: "bold red",
        LogLevel.UNKNOWN: "white",
    }

    def __init__(
        self,
        console: Optional[Console] = None,
        max_history: int = 1000,
        display_mode: DisplayMode = DisplayMode.TEXT,
    ):
        self.console = console or get_console()
        self.max_history = max_history
        self.display_mode = display_mode

        # 历史记录
        self.history: deque = deque(maxlen=max_history)

        # 串口连接
        self.serial_port: Optional[serial.Serial] = None
        self.port_name: str = ""
        self.baudrate: int = 115200
        self.connected: bool = False

        # 线程控制
        self._read_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

        # 统计
        self.bytes_received = 0
        self.lines_received = 0
        self.start_time: Optional[datetime] = None

        # 回调
        self.on_message: Optional[Callable[[SerialMessage], None]] = None

    def detect_level(self, data: bytes) -> LogLevel:
        """
        自动识别日志级别

        Args:
            data: 原始字节数据

        Returns:
            识别的日志级别
        """
        try:
            text = data.decode("utf-8", errors="ignore").upper()

            for level, patterns in self.LEVEL_PATTERNS.items():
                for pattern in patterns:
                    if pattern.upper() in text:
                        return level

            return LogLevel.UNKNOWN
        except:
            return LogLevel.UNKNOWN

    def connect(
        self,
        port: str,
        baudrate: int = 115200,
        timeout: float = 1.0,
    ) -> bool:
        """
        连接串口

        Args:
            port: 串口名称（如 COM3 或 /dev/ttyUSB0）
            baudrate: 波特率
            timeout: 超时时间

        Returns:
            是否连接成功
        """
        if not HAS_SERIAL:
            self.console.print("[red][X] pyserial not installed. Run: pip install pyserial[/red]")
            return False

        try:
            self.serial_port = serial.Serial(
                port=port,
                baudrate=baudrate,
                timeout=timeout,
            )

            self.port_name = port
            self.baudrate = baudrate
            self.connected = True
            self.start_time = datetime.now()

            # 启动读取线程
            self._stop_event.clear()
            self._read_thread = threading.Thread(target=self._read_loop, daemon=True)
            self._read_thread.start()

            return True

        except Exception as e:
            self.console.print(f"[red][X] Failed to connect: {e}[/red]")
            return False

    def disconnect(self) -> None:
        """断开连接"""
        self._stop_event.set()

        if self._read_thread and self._read_thread.is_alive():
            self._read_thread.join(timeout=2.0)

        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()

        self.connected = False
        self.serial_port = None

    def _read_loop(self) -> None:
        """后台读取线程"""
        buffer = b""

        while not self._stop_event.is_set():
            try:
                if self.serial_port and self.serial_port.is_open:
                    # 读取可用数据
                    data = self.serial_port.read(self.serial_port.in_waiting or 1)

                    if data:
                        buffer += data
                        self.bytes_received += len(data)

                        # 按行分割
                        while b"\n" in buffer:
                            line, buffer = buffer.split(b"\n", 1)
                            line = line.rstrip(b"\r")

                            if line:
                                msg = SerialMessage(
                                    timestamp=datetime.now(),
                                    data=line,
                                    level=self.detect_level(line),
                                )
                                self.history.append(msg)
                                self.lines_received += 1

                                # 调用回调
                                if self.on_message:
                                    self.on_message(msg)

                time.sleep(0.01)  # 10ms 轮询

            except Exception as e:
                if not self._stop_event.is_set():
                    self.console.print(f"[red][X] Read error: {e}[/red]")
                break

    def send(self, data: str or bytes) -> bool:
        """
        发送数据

        Args:
            data: 要发送的数据

        Returns:
            是否发送成功
        """
        if not self.connected or not self.serial_port:
            return False

        try:
            if isinstance(data, str):
                data = data.encode("utf-8")

            self.serial_port.write(data)
            return True
        except Exception as e:
            self.console.print(f"[red][X] Send error: {e}[/red]")
            return False

    def format_message(self, msg: SerialMessage) -> str:
        """
        格式化消息显示

        Args:
            msg: 消息对象

        Returns:
            格式化后的字符串
        """
        timestamp = msg.timestamp.strftime("%H:%M:%S.%f")[:-3]
        style = self.LEVEL_STYLES.get(msg.level, "white")

        if self.display_mode == DisplayMode.HEX:
            # 纯十六进制模式
            hex_data = msg.get_hex()
            return f"[{timestamp}] [{style}]{hex_data}[/{style}]"

        elif self.display_mode == DisplayMode.MIXED:
            # 混合模式
            text = msg.get_text()
            hex_data = msg.get_hex()
            return f"[{timestamp}] [{style}]{text}[/{style}]\n    [dim]{hex_data}[/dim]"

        else:
            # 纯文本模式（默认）
            text = msg.get_text()
            level_tag = f"[{msg.level.value}]" if msg.level != LogLevel.UNKNOWN else ""
            return f"[{timestamp}] [{style}]{level_tag} {text}[/{style}]"

    def render_history(self, max_lines: int = 50) -> str:
        """
        渲染历史记录

        Args:
            max_lines: 最大显示行数

        Returns:
            格式化后的历史记录
        """
        lines = []

        # 获取最近的消息
        recent = list(self.history)[-max_lines:]

        for msg in recent:
            lines.append(self.format_message(msg))

        return "\n".join(lines) if lines else "[dim]Waiting for data...[/dim]"

    def render_status(self) -> str:
        """渲染状态栏"""
        if self.connected:
            duration = ""
            if self.start_time:
                elapsed = datetime.now() - self.start_time
                duration = f" ({elapsed.seconds}s)"

            return (
                f"[green][OK][/green] {self.port_name} @ {self.baudrate} baud"
                f" | RX: {self.bytes_received} bytes, {self.lines_received} lines{duration}"
            )
        else:
            return "[dim]Disconnected[/dim]"

    def render(self, max_lines: int = 50) -> Panel:
        """
        渲染监控器面板

        Args:
            max_lines: 最大显示行数

        Returns:
            Rich Panel 对象
        """
        # 内容区域
        content = self.render_history(max_lines)

        # 状态栏
        status = self.render_status()

        # 组合
        full_content = f"{content}\n\n[dim]{'─' * 40}[/dim]\n{status}"

        return Panel(
            full_content,
            title="[bold cyan]Serial Monitor[/bold cyan]",
            border_style="cyan" if self.connected else "dim",
            box=box.ROUNDED,
            padding=(0, 1),
        )

    def start_live(self, refresh_rate: int = 10) -> None:
        """
        启动实时显示（阻塞）

        Args:
            refresh_rate: 刷新率（Hz）
        """
        if not self.connected:
            self.console.print("[red][X] Not connected[/red]")
            return

        try:
            with Live(
                self.render(),
                console=self.console,
                refresh_per_second=refresh_rate,
            ) as live:
                while self.connected:
                    live.update(self.render())
                    time.sleep(0.1)
        except KeyboardInterrupt:
            self.console.print("\n[yellow][!] Monitor stopped[/yellow]")

    @staticmethod
    def list_ports() -> List[dict]:
        """
        列出可用串口

        Returns:
            串口信息列表
        """
        if not HAS_SERIAL:
            return []

        ports = []
        for port in serial.tools.list_ports.comports():
            ports.append(
                {
                    "device": port.device,
                    "description": port.description,
                    "hwid": port.hwid,
                }
            )
        return ports

    @classmethod
    def select_port(cls, console: Optional[Console] = None) -> Optional[str]:
        """
        交互式选择串口

        Args:
            console: Console 实例

        Returns:
            选中的串口名称
        """
        console = console or get_console()
        ports = cls.list_ports()

        if not ports:
            console.print("[yellow][!] No serial ports found[/yellow]")
            return None

        # 显示列表
        table = Table(
            title="Available Serial Ports",
            border_style="cyan",
        )
        table.add_column("#", style="cyan", justify="right")
        table.add_column("Port", style="green")
        table.add_column("Description", style="white")

        for i, port in enumerate(ports, 1):
            table.add_row(
                str(i),
                port["device"],
                port["description"],
            )

        console.print(table)

        # 选择
        from rich.prompt import IntPrompt

        choice = IntPrompt.ask(
            "[cyan]Select port (number)[/cyan]",
            default=1,
        )

        if 1 <= choice <= len(ports):
            return ports[choice - 1]["device"]

        return None


def create_monitor(
    port: Optional[str] = None,
    baudrate: int = 115200,
    console: Optional[Console] = None,
) -> SerialMonitor:
    """
    便捷函数：创建并连接串口监控器

    Args:
        port: 串口名称，None 则交互式选择
        baudrate: 波特率
        console: Console 实例

    Returns:
        SerialMonitor 实例
    """
    console = console or get_console()
    monitor = SerialMonitor(console)

    if port is None:
        port = SerialMonitor.select_port(console)

    if port:
        if monitor.connect(port, baudrate):
            console.print(f"[green][OK] Connected to {port} @ {baudrate}[/green]")
        else:
            console.print(f"[red][X] Failed to connect to {port}[/red]")

    return monitor
