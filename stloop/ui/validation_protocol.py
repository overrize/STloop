"""
验证日志协议与解析

约定前缀与标签：
- SERIAL [FOC] / SERIAL [MOTOR] 等
- AGENT / SYSTEM
- CH1 / CH2（示波器通道）
- ✓ / ✗ 表示通过/失败
"""

import re
from dataclasses import dataclass
from enum import Enum
from typing import Optional

class ValidationSource(str, Enum):
    """验证日志来源（用于解析与高亮）"""
    SERIAL = "SERIAL"
    JTAG = "JTAG"
    LA = "LA"
    OSC = "OSC"
    AGENT = "AGENT"
    SYSTEM = "SYSTEM"
    CH1 = "CH1"
    CH2 = "CH2"
    CH3 = "CH3"
    CH4 = "CH4"
    RAW = "RAW"


@dataclass
class ValidationEvent:
    """解析后的验证事件"""
    source: ValidationSource
    tag: Optional[str] = None  # e.g. FOC, MOTOR
    message: str = ""
    passed: Optional[bool] = None  # True=✓, False=✗, None=无结果

    def source_style(self) -> str:
        """Rich 样式：按来源区分颜色"""
        if self.source == ValidationSource.SERIAL:
            return "#3498DB"  # serial
        if self.source == ValidationSource.JTAG:
            return "#F39C12"  # jtag
        if self.source == ValidationSource.LA:
            return "#1ABC9C"  # logic
        if self.source == ValidationSource.OSC or self.source.value.startswith("CH"):
            return "#9B59B6"  # scope
        if self.source == ValidationSource.AGENT:
            return "bold cyan"
        if self.source == ValidationSource.SYSTEM:
            return "bold green"
        return "white"

    def prefix_text(self) -> str:
        """显示用前缀，如 SERIAL [FOC] 或 AGENT"""
        if self.source == ValidationSource.SERIAL and self.tag:
            return f"SERIAL [{self.tag}]"
        if self.source in (ValidationSource.AGENT, ValidationSource.SYSTEM):
            return self.source.value
        if self.source.value.startswith("CH"):
            return self.source.value
        return self.source.value


# 匹配 SERIAL [FOC] / SERIAL [MOTOR] 等
_RE_SERIAL_TAG = re.compile(r"^SERIAL\s+\[([A-Z0-9_]+)\]\s*(.*)$", re.IGNORECASE)
# 匹配 AGENT / SYSTEM 开头
_RE_AGENT = re.compile(r"^AGENT\s+(.*)$", re.IGNORECASE)
_RE_SYSTEM = re.compile(r"^SYSTEM\s+(.*)$", re.IGNORECASE)
# 匹配 CH1 / CH2 / CH3 / CH4
_RE_CH = re.compile(r"^(CH[1-4])\s+(.*)$", re.IGNORECASE)
# 通过/失败标记
_PASS_MARKERS = ("✓", "✔", "PASS", "OK", "successful")
_FAIL_MARKERS = ("✗", "✘", "FAIL", "ERROR", "failed")


def _check_passed(message: str) -> Optional[bool]:
    """从消息中检测是否通过/失败"""
    msg_upper = message.upper()
    for m in _PASS_MARKERS:
        if m in message or m.upper() in msg_upper:
            return True
    for m in _FAIL_MARKERS:
        if m in message or m.upper() in msg_upper:
            return False
    return None


def parse_validation_line(raw_line: str) -> ValidationEvent:
    """
    将原始日志行解析为 ValidationEvent。

    支持格式示例：
    - SERIAL [FOC] Encoder offset: 47.3° electrical
    - SERIAL [MOTOR] Step command: 0 → 3000 RPM
    - AGENT Running test: D-Q axis current control
    - CH1 Phase current: sinusoidal, 2.1A peak ✓
    - SYSTEM HARDWARE VALIDATION PASSED • 5/5 tests successful
    """
    line = raw_line.strip()
    if not line:
        return ValidationEvent(source=ValidationSource.RAW, message=raw_line)

    # SERIAL [TAG] ...
    m = _RE_SERIAL_TAG.match(line)
    if m:
        tag, rest = m.group(1), m.group(2)
        return ValidationEvent(
            source=ValidationSource.SERIAL,
            tag=tag,
            message=rest,
            passed=_check_passed(rest),
        )

    # AGENT ...
    m = _RE_AGENT.match(line)
    if m:
        return ValidationEvent(
            source=ValidationSource.AGENT,
            message=m.group(1),
            passed=_check_passed(m.group(1)),
        )

    # SYSTEM ...
    m = _RE_SYSTEM.match(line)
    if m:
        return ValidationEvent(
            source=ValidationSource.SYSTEM,
            message=m.group(1),
            passed=_check_passed(m.group(1)),
        )

    # CH1 / CH2 / CH3 / CH4 ...
    m = _RE_CH.match(line)
    if m:
        ch, rest = m.group(1).upper(), m.group(2)
        src = ValidationSource[ch] if ch in ValidationSource.__members__ else ValidationSource.RAW
        return ValidationEvent(
            source=src,
            message=rest,
            passed=_check_passed(rest),
        )

    return ValidationEvent(source=ValidationSource.RAW, message=line, passed=_check_passed(line))
