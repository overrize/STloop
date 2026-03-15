"""编译失败后的自动修复策略。"""


def should_attempt_main_c_fix(error_text: str) -> tuple[bool, str]:
    """
    返回 (是否尝试修 main.c, 原因)。
    仅在疑似 C 源代码问题时触发自动修复，避免对工程配置类错误反复重试。
    """
    text = (error_text or "").lower()
    infra_markers = [
        "no linker script .ld",
        "startup_",
        "cmake error at",
        "cmake 配置失败",
        "stm32cube not found",
        "未找到 cmake",
        "toolchain",
        "arm-none-eabi-gcc: 未找到",
    ]
    if any(m in text for m in infra_markers):
        return False, "检测到构建基础设施问题（非 main.c 代码错误）"

    code_markers = [
        "main.c:",
        "/main.c:",
        "\\main.c:",
        ".c:",
        " error:",
        "undefined reference",
    ]
    if any(m in text for m in code_markers):
        return True, "检测到疑似 C 代码错误，尝试修复 main.c"

    return False, "未识别为可自动修复的 main.c 错误"
