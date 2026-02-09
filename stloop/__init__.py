"""
STLoop — STM32 自然语言端到端开发 Client
"""
__version__ = "0.1.0"
from .client import STLoopClient
from .errors import (
    BuildError,
    ConfigurationError,
    HardwareError,
    LLMError,
    STLoopError,
)

__all__ = [
    "STLoopClient",
    "STLoopError",
    "ConfigurationError",
    "BuildError",
    "LLMError",
    "HardwareError",
    "__version__",
]
