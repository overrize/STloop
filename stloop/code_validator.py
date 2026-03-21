"""LLM 生成代码的安全检查与质量校验"""

import re
import logging
from typing import NamedTuple

log = logging.getLogger("stloop")


class ValidationResult(NamedTuple):
    ok: bool
    warnings: list[str]
    errors: list[str]


_DANGEROUS_PATTERNS: list[tuple[str, str]] = [
    (r"system\s*\(", "system() — 嵌入式代码不应调用系统命令"),
    (r"exec[lv]?[pe]?\s*\(", "exec*() — 禁止进程替换调用"),
    (r"popen\s*\(", "popen() — 禁止管道命令"),
    (r"fork\s*\(", "fork() — 嵌入式无进程模型"),
    (r"dlopen\s*\(", "dlopen() — 嵌入式无动态链接"),
]

_SUSPICIOUS_INCLUDES: list[str] = [
    "<stdlib.h>",
    "<unistd.h>",
    "<dlfcn.h>",
    "<sys/socket.h>",
    "<netinet/in.h>",
]


def check_code_safety(code: str) -> tuple[bool, list[str]]:
    """检查 LLM 生成代码是否含有危险模式。

    Returns:
        (is_safe, list_of_warnings)
    """
    warnings: list[str] = []

    for pat, desc in _DANGEROUS_PATTERNS:
        if re.search(pat, code):
            warnings.append(f"检测到可疑调用: {desc}")

    if re.search(r"HAL_\w+", code):
        warnings.append("代码包含 HAL 库调用，应使用 LL 库")

    if "__asm" in code or re.search(r"\basm\s*\(", code):
        warnings.append("代码包含内联汇编，请人工审查")

    for inc in _SUSPICIOUS_INCLUDES:
        if inc in code:
            warnings.append(f"可疑头文件: #include {inc} 通常不用于裸机固件")

    return (len(warnings) == 0, warnings)


def validate_generated_code(code: str) -> ValidationResult:
    """对生成的 C 代码做结构性质量校验。

    Returns:
        ValidationResult(ok, warnings, errors)
        - errors 非空表示代码有严重缺陷，不应直接使用
        - warnings 非空表示有潜在问题但不阻塞
    """
    warnings: list[str] = []
    errors: list[str] = []

    stripped = code.strip()
    if not stripped:
        errors.append("生成代码为空")
        return ValidationResult(False, warnings, errors)

    line_count = stripped.count("\n") + 1
    if line_count < 10:
        errors.append(f"代码过短（{line_count} 行），可能不完整")
    elif line_count > 2000:
        warnings.append(f"代码异常长（{line_count} 行），建议人工审查")

    if "int main" not in code and "void main" not in code:
        errors.append("缺少 main 函数入口")

    opens = code.count("{")
    closes = code.count("}")
    if opens != closes:
        errors.append(f"大括号不匹配: {{ 出现 {opens} 次, }} 出现 {closes} 次")

    has_clock_init = any(
        kw in code
        for kw in [
            "SystemClock_Config",
            "LL_RCC_HSE_Enable",
            "LL_RCC_PLL_Enable",
            "RCC_OscInitStruct",
            "SetSystemCoreClock",
        ]
    )
    if not has_clock_init:
        warnings.append("未检测到时钟初始化代码，固件可能无法正常运行")

    if not re.search(r'#include\s+[<"]', code):
        warnings.append("未检测到任何 #include 指令")

    ok = len(errors) == 0
    return ValidationResult(ok, warnings, errors)
