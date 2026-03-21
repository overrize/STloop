"""LLM 接口 — Zephyr RTOS 代码生成"""

import logging
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

ZEPHYR_SYSTEM_PROMPT = """你是 Zephyr RTOS 嵌入式开发专家。

生成 Zephyr 代码必须遵循：

1. **头文件**（必须包含）：
   #include <zephyr/kernel.h>
   #include <zephyr/drivers/gpio.h>
   #include <zephyr/sys/printk.h>

2. **硬件访问**（使用 Device Tree）：
   #define LED0_NODE DT_ALIAS(led0)
   static const struct gpio_dt_spec led = GPIO_DT_SPEC_GET(LED0_NODE, gpios);

3. **GPIO 操作**：
   - 检查: gpio_is_ready_dt(&led)
   - 配置: gpio_pin_configure_dt(&led, GPIO_OUTPUT_ACTIVE)
   - 控制: gpio_pin_set_dt(&led, 1) / gpio_pin_toggle_dt(&led)
   - 读取: gpio_pin_get_dt(&button)

4. **定时**：
   - k_msleep(1000) - 毫秒延时
   - k_sleep(K_SECONDS(1)) - 秒延时

5. **主函数**：
   int main(void) {
       if (!gpio_is_ready_dt(&led)) return -1;
       gpio_pin_configure_dt(&led, GPIO_OUTPUT_ACTIVE);
       while (1) {
           gpio_pin_toggle_dt(&led);
           k_msleep(500);
       }
       return 0;
   }

6. **多线程**（可选）：
   K_THREAD_DEFINE(thread_id, 1024, thread_fn, NULL, NULL, NULL, 5, 0, 0);

7. **输出格式**：仅输出 C 代码，不要 markdown 或解释

8. **禁止**：system()、exec()、popen()、stdlib.h
"""


def generate_code(prompt: str, board: str, **kwargs) -> str:
    """生成 Zephyr 代码"""
    if OpenAI is None:
        raise RuntimeError("请安装 openai: pip install openai")

    cfg_key, cfg_base, cfg_model = get_llm_config(kwargs.get("work_dir"))
    api_key = kwargs.get("api_key") or cfg_key
    base_url = kwargs.get("base_url") or cfg_base
    model = kwargs.get("model") or cfg_model

    if not api_key:
        raise ValueError("未设置 OPENAI_API_KEY")

    client_kw = {"api_key": api_key}
    if base_url:
        client_kw["base_url"] = base_url.rstrip("/")

    client = OpenAI(**client_kw)

    user_content = f"Board: {board}\\n需求: {prompt}"

    log.info("生成代码: board=%s, model=%s", board, model)

    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": ZEPHYR_SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
        temperature=0.2,
    )

    content = resp.choices[0].message.content or ""

    # 提取代码块
    if "```c" in content:
        content = content.split("```c", 1)[1].split("```", 1)[0].strip()
    elif "```" in content:
        content = content.split("```", 1)[1].split("```", 1)[0].strip()

    return content
