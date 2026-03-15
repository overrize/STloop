"""
验证数据源抽象与实现

- ValidationDataSource: 抽象基类，产出日志行并推送到验证视图
- SerialValidationSource: 串口（pyserial）
- JTAGValidationSource: pyOCD 实时数据（内存/变量轮询）
- LogicAnalyzerPlaceholder / OscilloscopePlaceholder: 占位
"""

from abc import ABC, abstractmethod
from typing import Callable, Optional

from stloop.ui.validation_view import ValidationChannel


class ValidationDataSource(ABC):
    """验证数据源抽象：连接、断开、推送日志行到回调"""

    channel: ValidationChannel

    @abstractmethod
    def connect(self, **kwargs) -> bool:
        """连接数据源。返回是否成功。"""
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """断开连接"""
        pass

    @abstractmethod
    def is_connected(self) -> bool:
        """是否已连接"""
        pass

    def set_on_line(self, callback: Callable[[str], None]) -> None:
        """设置收到一行日志时的回调（来源前缀由调用方或协议解析识别）"""
        self._on_line = callback

    def _emit(self, line: str) -> None:
        if getattr(self, "_on_line", None):
            self._on_line(line)


class SerialValidationSource(ValidationDataSource):
    """串口数据源：包装 pyserial，按行推送"""

    channel = ValidationChannel.SERIAL

    def __init__(self, port: str = "", baudrate: int = 115200):
        self.port = port
        self.baudrate = baudrate
        self._serial = None
        self._on_line = None
        self._running = False
        self._thread = None

    def connect(self, port: Optional[str] = None, baudrate: Optional[int] = None, **kwargs) -> bool:
        if port is not None:
            self.port = port
        if baudrate is not None:
            self.baudrate = baudrate
        if not self.port:
            return False
        try:
            import serial
            self._serial = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=kwargs.get("timeout", 1.0),
            )
            self._running = True
            import threading
            self._thread = threading.Thread(target=self._read_loop, daemon=True)
            self._thread.start()
            return True
        except Exception:
            return False

    def _read_loop(self) -> None:
        import time
        buffer = b""
        while self._running and self._serial and self._serial.is_open:
            try:
                data = self._serial.read(self._serial.in_waiting or 1)
                if data:
                    buffer += data
                    while b"\n" in buffer:
                        line, buffer = buffer.split(b"\n", 1)
                        line = line.rstrip(b"\r")
                        if line:
                            try:
                                text = line.decode("utf-8", errors="replace")
                                self._emit(text)
                            except Exception:
                                self._emit(line.hex())
                else:
                    time.sleep(0.01)
            except Exception:
                break

    def disconnect(self) -> None:
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        if self._serial and self._serial.is_open:
            try:
                self._serial.close()
            except Exception:
                pass
        self._serial = None

    def is_connected(self) -> bool:
        return self._serial is not None and self._serial.is_open


class JTAGValidationSource(ValidationDataSource):
    """JTAG/SWD 数据源：pyOCD 会话，轮询内存/变量并推送为日志行"""

    channel = ValidationChannel.JTAG

    def __init__(self, target_override: str = "stm32f411re", probe_id: Optional[str] = None):
        self.target_override = target_override
        self.probe_id = probe_id
        self._session = None
        self._on_line = None
        self._running = False
        self._thread = None

    def connect(self, target_override: Optional[str] = None, probe_id: Optional[str] = None, **kwargs) -> bool:
        if target_override is not None:
            self.target_override = target_override
        if probe_id is not None:
            self.probe_id = probe_id
        try:
            from pyocd.core.helpers import ConnectHelper
            options = {"frequency": 4_000_000, "target_override": self.target_override}
            if self.probe_id:
                options["unique_id"] = self.probe_id
            self._session = ConnectHelper.session_with_chosen_probe(options=options)
            self._session.__enter__()
            self._running = True
            poll_interval = kwargs.get("poll_interval", 0.5)
            addr = kwargs.get("poll_address")
            if addr is not None:
                import threading
                self._thread = threading.Thread(
                    target=self._poll_loop,
                    args=(addr, kwargs.get("poll_size", 4), poll_interval),
                    daemon=True,
                )
                self._thread.start()
            return True
        except Exception:
            if self._session is not None:
                try:
                    self._session.__exit__(None, None, None)
                except Exception:
                    pass
                self._session = None
            return False

    def _poll_loop(self, addr: int, size: int, interval: float) -> None:
        import time
        while self._running and self._session:
            try:
                target = self._session.target
                if target.is_running():
                    value = target.read_memory(addr, size)
                    if size == 4 and len(value) >= 4:
                        v = int.from_bytes(value[:4], "little")
                        self._emit(f"JTAG mem 0x{addr:x}: 0x{v:08x}")
                time.sleep(interval)
            except Exception as e:
                self._emit(f"JTAG poll error: {e}")
                break

    def disconnect(self) -> None:
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        if self._session is not None:
            try:
                self._session.__exit__(None, None, None)
            except Exception:
                pass
            self._session = None

    def is_connected(self) -> bool:
        return self._session is not None


class LogicAnalyzerPlaceholder(ValidationDataSource):
    """逻辑分析仪占位：不连接，可注入模拟行或对接外部脚本"""

    channel = ValidationChannel.LA

    def __init__(self) -> None:
        self._on_line = None
        self._connected = False

    def connect(self, **kwargs) -> bool:
        self._connected = True
        self._emit("LA placeholder: connect external tool or script for logic analyzer data.")
        return True

    def disconnect(self) -> None:
        self._connected = False

    def is_connected(self) -> bool:
        return self._connected


class OscilloscopePlaceholder(ValidationDataSource):
    """示波器占位：不连接，可注入模拟行或对接外部工具"""

    channel = ValidationChannel.OSC

    def __init__(self) -> None:
        self._on_line = None
        self._connected = False

    def connect(self, **kwargs) -> bool:
        self._connected = True
        self._emit("OSC placeholder: connect external scope or script for channel data (CH1, CH2, ...).")
        return True

    def disconnect(self) -> None:
        self._connected = False

    def is_connected(self) -> bool:
        return self._connected
