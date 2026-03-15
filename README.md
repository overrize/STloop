# STLoop — STM32 AI Firmware Engineer

自然语言驱动 STM32 固件开发。描述需求 → AI 生成代码 → 自动编译 → 烧录/仿真 → 验证测试。

## 快速开始

```bash
# 安装
pip install -e .

# 配置 API (复制 .env.example → .env)
OPENAI_API_KEY=sk-xxx
OPENAI_API_BASE=https://api.moonshot.cn/v1  # Kimi

# 启动交互式开发
python -m stloop
```

## 核心功能

| 功能 | 命令 |
|------|------|
| 交互式开发 | `python -m stloop` |
| 生成+编译+烧录 | `stloop gen "PA5 LED闪烁" --build --flash` |
| 硬件仿真 (无需硬件) | `stloop gen "PA5 LED闪烁" --build --sim` |
| 硬件目录 | `stloop catalog` |
| 环境检查 | `stloop check` |
| 串口监控 | `stloop monitor` |

## 前置依赖

```bash
# 必需: 编译工具链
arm-none-eabi-gcc  # https://developer.arm.com/downloads/-/gnu-rm
cmake >= 3.15

# 可选: 烧录调试
pyocd  # pip install pyocd

# 可选: 硬件仿真
renode  # https://renode.io (已内置 STM32F4 支持)
```

## 使用示例

### 1. 交互式开发 (推荐)
```bash
$ python -m stloop

Step 1: Hardware Selection
Available MCUs: STM32F411RE, STM32F407VG, STM32F446RE, ESP32-S3...
Select MCU (number): 1

Step 2: Requirement
Your requirement: PA5 LED blink 1Hz

Step 3: Additional Resources (Optional)
Schematic path (Enter to skip): 
Datasheet PDFs (comma-separated, Enter to skip): 

Step 4: Preparing Dependencies
[OK] STM32CubeF4 found

Step 5: Code Generation
Generating code...
[OK] Code generated at: projects/generated/

Step 6: Build
Building with CMake...
[OK] Build successful: build/firmware.elf

Step 7: Deploy & Test
Choose how to run your firmware:
  1. Flash to real hardware (requires ST-Link)
  2. Simulate with Renode (no hardware needed)  <-- 默认
  3. Skip (build only)
Select option [2]: 

[OK] Renode found
[OK] Platform: platforms/cpus/stm32f411.repl
[OK] Generated: simulation.resc
Starting simulation...
[OK] Simulation completed successfully
```

### 2. 一键生成+烧录
```bash
# 生成、编译、烧录到硬件
stloop gen "UART1 echo at 115200" --build --flash

# 烧录后启动串口监控
stloop gen "ADC read PA0" --build --flash --monitor
```

### 3. 硬件仿真 (无需物理硬件)
```bash
# 生成、编译、仿真
stloop gen "TIM2 PWM PA5 1kHz" --build --sim --mcu STM32F411RE

# 单独仿真已有固件
stloop sim build/firmware.elf --mcu STM32F407VG --gui

# 查看支持的 MCU
stloop sim --mcu list
```

## 技术栈

- **代码生成**: LLM (Kimi/OpenAI/兼容 OpenAI API)
- **HAL 库**: STM32 LL 库 (Low Layer)
- **构建系统**: CMake + arm-none-eabi-gcc
- **烧录调试**: pyOCD + ST-Link
- **硬件仿真**: Renode (STM32F4 系列)
- **串口监控**: pyserial

## 支持的 MCU

| 系列 | 型号 | 状态 |
|------|------|------|
| STM32F4 | F411RE, F407VG, F405RG, F446RE | ✅ 完整支持 |
| ESP32 | S3, C3 | ✅ 支持 |
| nRF52 | nRF52840 | ✅ 支持 |
| RP2040 | Pico | ✅ 支持 |

## 项目结构

```
stloop/
├── stloop/
│   ├── client.py       # 核心 API
│   ├── cli_rich.py     # 命令行界面
│   ├── chat_rich.py    # 交互式终端
│   ├── simulators/     # 硬件仿真 (Renode)
│   ├── ui/            # 可视化组件
│   └── hardware/      # MCU 数据库
├── templates/         # CMake 工程模板
├── demos/            # 示例项目
└── docs/            # 文档
```

## API 使用

```python
from stloop import STLoopClient

client = STLoopClient()

# 运行 Demo
elf = client.demo_blink(flash=True)

# 构建项目
elf = client.build("my_project/")

# 烧录固件
client.flash(elf)

# 硬件仿真 (无需硬件)
from stloop.simulators import RenodeSimulator
sim = RenodeSimulator()
sim.start(elf, mcu="STM32F411RE")
```

## 故障排除

```bash
# 检查环境
stloop check

# 下载 STM32CubeF4
stloop cube-download

# 调试模式
stloop -v gen "test" --build
```

## 文档

- [开发经验](docs/LESSONS.md) - 踩坑记录
- [Renode 仿真计划](docs/RENODE_PLAN.md) - 仿真功能详情
- [决策清单](docs/DECISION_CHECKLIST.md) - 设计决策

## License

MIT
