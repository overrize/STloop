"""大模型接口 — 用于代码生成（支持 OpenAI、Kimi 等兼容 API）"""
from pathlib import Path
from typing import Optional

from .llm_config import get_llm_config

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

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
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.2,
    )
    content = resp.choices[0].message.content or ""
    if "```c" in content:
        content = content.split("```c", 1)[1].split("```", 1)[0].strip()
    elif "```" in content:
        content = content.split("```", 1)[1].split("```", 1)[0].strip()
    return content
