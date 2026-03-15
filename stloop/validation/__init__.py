"""
真实世界验证模块

- 数据源抽象与实现（串口、JTAG、LA、OSC）
- 测试用例与 Agent 调度（validation_agent.py）
- 报告生成（report.py）
"""

from .data_sources import (
    ValidationDataSource,
    SerialValidationSource,
    JTAGValidationSource,
    LogicAnalyzerPlaceholder,
    OscilloscopePlaceholder,
)
from .validation_agent import ValidationAgent, ValidationTestCase
from .hardware_topology import ValidationTopology

__all__ = [
    "ValidationDataSource",
    "SerialValidationSource",
    "JTAGValidationSource",
    "LogicAnalyzerPlaceholder",
    "OscilloscopePlaceholder",
    "ValidationAgent",
    "ValidationTestCase",
]
