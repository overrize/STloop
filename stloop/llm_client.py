"""大模型接口 — 用于代码生成（支持 OpenAI、Kimi 等兼容 API）"""

import logging
import re
from pathlib import Path
from typing import Optional

from .errors import LLMError
from .llm_config import get_llm_config

log = logging.getLogger("stloop")

try:
    from openai import APIError, APIStatusError, OpenAI
except ImportError:
    OpenAI = None
    APIError = Exception
    APIStatusError = Exception

API_BASE_HINT = """
若使用 Kimi/Moonshot，请在 .env 中添加：
  OPENAI_API_BASE=https://api.moonshot.cn/v1
  OPENAI_MODEL=kimi-k2-0905-preview
获取 Key: https://platform.moonshot.cn/console/api-keys
"""


def check_code_safety(code: str) -> tuple[bool, list[str]]:
    """检查 LLM 生成代码的安全性。返回 (是否安全, 警告列表)"""
    warnings: list[str] = []
    # 危险系统调用（嵌入式不应包含）
    dangerous = [
        (r"system\s*\(", "system()"),
        (r"exec[lv]?\s*\(", "exec*()"),
        (r"popen\s*\(", "popen()"),
    ]
    for pat, name in dangerous:
        if re.search(pat, code):
            warnings.append(f"检测到可疑调用: {name}")

    if re.search(r"HAL_\w+", code):
        warnings.append("代码包含 HAL 库调用，应使用 LL 库")

    if "__asm" in code or re.search(r"\basm\s*\(", code):
        warnings.append("代码包含内联汇编，请人工审查")

    return (len(warnings) == 0, warnings)


SYSTEM_PROMPT = """你是一名嵌入式工程师，专门使用 STM32 LL（Low-Level）库开发固件。

## 代码要求
1. **仅使用 LL 库**：LL_GPIO_*, LL_RCC_*, LL_UTILS_* 等，禁止使用 HAL
2. **必须包含头文件**：
   #include "main.h"
   #include "stm32f4xx_ll_gpio.h"
   #include "stm32f4xx_ll_bus.h"
   #include "stm32f4xx_ll_rcc.h"
   #include "stm32f4xx_ll_system.h"
   #include "stm32f4xx_ll_utils.h"
3. **时钟配置**：
   - HSE = 8MHz（Nucleo 板载晶振）
   - PLL 配置到 100MHz（F411RE 最大频率）
   - 必须等待 HSE/PLL 就绪（while (!LL_RCC_HSE_IsReady()); 等）
4. **代码结构**：
   - 包含 SystemClock_Config() 和外设初始化函数
   - main() 中先调用时钟配置，再初始化外设
5. **输出格式**：仅输出 C 代码，不要 markdown 标记或解释文字

## 示例（LED 闪烁 PA5）
```c
#include "main.h"
#include "stm32f4xx_ll_gpio.h"
#include "stm32f4xx_ll_bus.h"
#include "stm32f4xx_ll_utils.h"

static void SystemClock_Config(void);

int main(void) {
    SystemClock_Config();
    LL_AHB1_GRP1_EnableClock(LL_AHB1_GRP1_PERIPH_GPIOA);
    LL_GPIO_SetPinMode(GPIOA, LL_GPIO_PIN_5, LL_GPIO_MODE_OUTPUT);
    while (1) {
        LL_GPIO_TogglePin(GPIOA, LL_GPIO_PIN_5);
        LL_mDelay(500);
    }
}

static void SystemClock_Config(void) {
    LL_FLASH_SetLatency(LL_FLASH_LATENCY_2);
    LL_RCC_HSE_Enable();
    while (!LL_RCC_HSE_IsReady());
    LL_RCC_PLL_ConfigDomain_SYS(LL_RCC_PLLSOURCE_HSE, LL_RCC_PLLM_DIV_4, 100, LL_RCC_PLLP_DIV_2);
    LL_RCC_PLL_Enable();
    while (!LL_RCC_PLL_IsReady());
    LL_RCC_SetSysClkSource(LL_RCC_SYS_CLKSOURCE_PLL);
    while (LL_RCC_GetSysClkSource() != LL_RCC_SYS_CLKSOURCE_STATUS_PLL);
    LL_SetSystemCoreClock(100000000);
}
```

根据用户需求生成代码。"""


def generate_main_c(
    user_prompt: str,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    model: Optional[str] = None,
    work_dir: Optional[Path] = None,
) -> str:
    """根据自然语言需求生成 main.c 内容。支持 OpenAI、Kimi(Moonshot) 等兼容 API"""
    if OpenAI is None:
        raise RuntimeError("请安装 openai: pip install openai")

    cfg_key, cfg_base, cfg_model = get_llm_config(work_dir)
    api_key = api_key or cfg_key
    base_url = base_url or cfg_base
    model = model or cfg_model

    if not api_key:
        raise ValueError(
            "未设置 OPENAI_API_KEY 或 STLOOP_API_KEY，请先配置。运行 python -m stloop 查看配置说明。"
        )

    client_kw = {"api_key": api_key}
    if base_url:
        client_kw["base_url"] = base_url.rstrip("/")

    client = OpenAI(**client_kw)
    log.info("模型: %s, base: %s", model, base_url or "default")
    print(f"  [生成] 使用模型: {model}")
    print("  [生成] 正在调用 API...")
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
        )
    except (APIStatusError, APIError) as e:
        err_msg = str(e).lower()
        if "401" in err_msg or "invalid_api_key" in err_msg:
            if not base_url:
                raise LLMError(
                    f"API Key 无效或未设置。\n请在 .env 中配置 OPENAI_API_KEY。{API_BASE_HINT}"
                ) from e
            raise LLMError(
                f"API Key 无效（{base_url}）。请检查 .env 中的 OPENAI_API_KEY 是否正确。"
            ) from e
        if "429" in str(e) or "rate_limit" in err_msg:
            raise LLMError("API 请求频率超限，请稍后重试。") from e
        if "timeout" in err_msg:
            raise LLMError("API 请求超时，请检查网络连接。") from e
        raise LLMError(f"API 调用失败: {str(e)[:200]}") from e
    content = resp.choices[0].message.content or ""
    log.debug("原始响应长度: %d", len(content))
    print(f"  [生成] 收到响应 ({len(content)} 字符)")
    if "```c" in content:
        content = content.split("```c", 1)[1].split("```", 1)[0].strip()
    elif "```" in content:
        content = content.split("```", 1)[1].split("```", 1)[0].strip()
    log.info("解析后代码长度: %d", len(content))
    lines = content.count("\n") + 1 if content else 0
    print(f"  [生成] 解析代码块完成，输出 {lines} 行")

    safe, warnings = check_code_safety(content)
    if not safe:
        for w in warnings:
            log.warning("生成代码安全检查: %s", w)
            print(f"  [警告] {w}")

    return content


FIX_SYSTEM_PROMPT = """你是一名嵌入式工程师。用户提供的 STM32 C 代码编译失败，你需要根据编译错误修正代码。
- 仅使用 STM32 LL 库 API，不使用 HAL
- 根据错误信息定位问题并修正（如头文件、符号、类型、语法等）
- 只输出修正后的完整 C 代码，不要解释
"""


def generate_main_c_fix(
    original_prompt: str,
    current_code: str,
    build_error: str,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    model: Optional[str] = None,
    work_dir: Optional[Path] = None,
) -> str:
    """根据编译错误修正 main.c，返回修正后的代码"""
    if OpenAI is None:
        raise RuntimeError("请安装 openai: pip install openai")

    cfg_key, cfg_base, cfg_model = get_llm_config(work_dir)
    api_key = api_key or cfg_key
    base_url = base_url or cfg_base
    model = model or cfg_model

    if not api_key:
        raise ValueError("未设置 OPENAI_API_KEY 或 STLOOP_API_KEY")

    user_content = f"""【原始需求】
{original_prompt}

【当前 main.c 代码（编译失败）】
```c
{current_code}
```

【编译错误】
{build_error}

请根据上述编译错误修正代码，只输出修正后的完整 C 代码，不要解释。"""

    client_kw = {"api_key": api_key}
    if base_url:
        client_kw["base_url"] = base_url.rstrip("/")
    client = OpenAI(**client_kw)

    log.info("修复编译错误，模型: %s", model)
    print("  [修复] 根据编译错误请求模型修正...")
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": FIX_SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
        temperature=0.1,
    )
    content = resp.choices[0].message.content or ""
    if "```c" in content:
        content = content.split("```c", 1)[1].split("```", 1)[0].strip()
    elif "```" in content:
        content = content.split("```", 1)[1].split("```", 1)[0].strip()
    log.info("修复后代码长度: %d", len(content))
    print(f"  [修复] 收到修正代码 ({len(content)} 字符)")
    return content
