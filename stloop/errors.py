"""STLoop 异常层次 — 统一错误处理"""


class STLoopError(Exception):
    """STLoop 基础异常"""

    pass


class ConfigurationError(STLoopError):
    """配置错误（用户可修复，如 cube 未下载、工具链缺失）"""

    pass


class BuildError(STLoopError):
    """编译错误（CMake 配置或 arm-none-eabi-gcc 编译失败）"""

    pass


class LLMError(STLoopError):
    """LLM 相关错误（API 调用失败、认证失败等）"""

    pass


class HardwareError(STLoopError):
    """硬件相关错误（烧录、调试器连接失败等）"""

    pass
