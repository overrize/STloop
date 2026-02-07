# STLoop — STM32 自然语言端到端开发

基于 LL 库 + CMake + pyOCD 的嵌入式开发 Client，通过自然语言描述需求，由大模型生成代码、自动编译、烧录、调试与测试。

## 能力概览

- **编码**：STM32 LL 库 + CMake 工程
- **编译**：CMake + arm-none-eabi-gcc
- **烧录/调试**：pyOCD
- **自动化测试**：pyOCD Python API
- **目标**：具备初级工程师的验证能力，快速验证硬件设计

## 前置条件

- Python 3.10+
- [arm-none-eabi-gcc](https://developer.arm.com/downloads/-/gnu-rm)
- [CMake](https://cmake.org/) 3.15+
- [pyOCD](https://pyocd.io/) + ST-Link 调试器
- STM32CubeF4 软件包（或通过 `python -m stloop cube-download` 自动下载）

## 快速开始

```bash
# 1. 安装 Client（推荐）
pip install -e .

# 可选：支持原理图/芯片手册 PDF 解析
pip install -e ".[pdf]"

# 2. 运行（推荐使用 python -m，避免 PATH 问题）
python -m stloop              # 交互式终端
python -m stloop demo blink   # Demo
python -m stloop demo blink --flash
```

> **说明**：若直接输入 `stloop` 提示找不到命令，请使用 `python -m stloop`。Windows 下 Scripts 目录可能不在 PATH 中。

## 大模型配置（chat / gen 需要）

交互式生成代码前需配置 API。复制 `.env.example` 为 `.env` 并填入。

**Kimi K2**（推荐，见 [官方文档](https://platform.moonshot.cn/docs/guide/agent-support)）：

```bash
OPENAI_API_KEY=sk-xxx
OPENAI_API_BASE=https://api.moonshot.cn/v1
OPENAI_MODEL=kimi-k2-0905-preview   # 或 kimi-k2-turbo-preview
```

**OpenAI**：`OPENAI_API_KEY=sk-xxx` 即可。

支持任意兼容 OpenAI 格式的 API。未配置时运行 `python -m stloop` 会显示完整配置说明。

## 项目结构

```
stloop/
├── stloop/           # Client 包
│   ├── client.py     # STLoopClient 可编程 API
│   ├── cli.py        # CLI 入口
│   ├── builder.py
│   ├── flasher.py
│   ├── tester.py
│   └── llm_client.py
├── config/           # 配置文件
├── templates/        # STM32 CMake + LL 工程模板
├── demos/            # 预置 Demo
├── main.py           # 向后兼容入口
└── pyproject.toml    # 包配置
```

## 可编程 API

```python
from stloop import STLoopClient

client = STLoopClient(work_dir=".")
client.ensure_cube()
elf = client.demo_blink(flash=True)
# 或
elf = client.build("demos/blink")
client.flash(elf)
```

## 使用流程

1. **提供输入**：原理图、芯片手册、连接调试器
2. **描述需求**：自然语言（如「PA5 控制 LED 闪烁」）
3. **大模型分析**：解析需求并生成 LL 库代码
4. **自动编译**：CMake 构建
5. **烧录运行**：pyOCD 烧录到设备
6. **自动化测试**：验证 GPIO/UART 等行为

## 目标芯片

默认支持 STM32F411RE（Nucleo-F411RE）。可扩展其他 F4 系列。

## License

MIT
