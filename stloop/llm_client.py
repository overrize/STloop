"""大模型接口 — 用于代码生成（支持 OpenAI、Kimi 等兼容 API）"""
import logging
from pathlib import Path
from typing import Optional

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

SYSTEM_PROMPT = """你是一名嵌入式工程师，专门使用 STM32 LL（Low-Level）库开发固件。
用户会描述硬件需求（如 GPIO、LED、外设等），你需要生成对应的 C 代码。

要求：
- 仅使用 STM32 LL 库 API（如 LL_GPIO_*, LL_RCC_*），不使用 HAL
- 目标芯片默认 STM32F411RE（Cortex-M4, 100MHz）
- 代码需包含必要的时钟配置、GPIO 初始化
- 只输出可编译的 C 代码，不要解释性文字
- 头文件使用：stm32f4xx.h, stm32f4xx_ll_gpio.h, stm32f4xx_ll_bus.h, stm32f4xx_ll_utils.h
"""


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
        raise ValueError("未设置 OPENAI_API_KEY 或 STLOOP_API_KEY，请先配置。运行 python -m stloop 查看配置说明。")

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
        err_msg = str(e)
        if "401" in err_msg or "invalid_api_key" in err_msg.lower():
            if not base_url:
                raise RuntimeError(
                    f"API 认证失败（401）。当前未设置 OPENAI_API_BASE，请求发往 OpenAI。{API_BASE_HINT}"
                ) from e
        raise
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
