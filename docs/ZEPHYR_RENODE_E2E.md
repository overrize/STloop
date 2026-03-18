# Zephyr + Renode 端到端测试指南

本文档介绍如何使用 STLoop 工具链完成 Zephyr 项目构建并在 Renode 中仿真运行。

## 前置条件

### 必需工具

| 工具 | 版本要求 | 安装方式 |
|------|----------|----------|
| Python | 3.10+ | https://python.org |
| West | 最新版 | `pip install west` |
| CMake | 3.20+ | https://cmake.org |
| Ninja | 1.10+ | 随 ARM GCC 或单独安装 |
| ARM GCC | 最新版 | https://developer.arm.com/downloads/-/arm-gnu-toolchain-downloads |
| Renode | 1.15+ | https://renode.io |

### 环境变量配置

```bash
# Windows (PowerShell)
$env:ZEPHYR_BASE = "E:\zephyr-workspace\zephyr"
$env:GNUARMEMB_TOOLCHAIN_PATH = "E:\arm_nobi"
$env:PATH += ";C:\Users\<用户名>\AppData\Roaming\Python\Python314\Scripts"

# Windows (CMD)
set ZEPHYR_BASE=E:\zephyr-workspace\zephyr
set GNUARMEMB_TOOLCHAIN_PATH=E:\arm_nobi
set PATH=%PATH%;C:\Users\<用户名>\AppData\Roaming\Python\Python314\Scripts
```

## 快速开始

### 1. 一键测试

```bash
cd E:\bitloop_embedderdev-kind
python test_zephyr_renode_e2e.py
```

### 2. 分步操作

#### 步骤 1: 检查环境

```bash
# 检查工具链
stloop check

# 验证 Zephyr 环境
python -c "from stloop.builder import check_zephyr_environment; print(check_zephyr_environment())"
```

#### 步骤 2: 构建项目

```bash
# 使用 stloop 构建
cd test_zephyr
stloop build . --board nucleo_f411re
```

或使用 Python API:

```python
from pathlib import Path
from stloop.builder import build

project_dir = Path("test_zephyr")
elf_path = build(project_dir, board="nucleo_f411re", use_zephyr=False)
print(f"构建成功: {elf_path}")
```

#### 步骤 3: 生成 Renode 脚本

```python
from pathlib import Path
from stloop.simulators.renode import generate_resc_script, RenodeConfig

elf_path = Path("test_zephyr/build/stloop_zephyr_compat.elf.exe")
config = RenodeConfig(mcu="STM32F411RE", show_gui=False, enable_uart=True)
script_path = generate_resc_script(elf_path, mcu="STM32F411RE", config=config)
print(f"脚本生成: {script_path}")
```

#### 步骤 4: 运行仿真

```bash
renode --console test_zephyr/build/simulation.resc
```

## 项目结构

```
test_zephyr/                    # Zephyr 兼容项目
├── src/
│   └── main.c                  # LED 闪烁示例代码
├── CMakeLists.txt              # CMake 配置
├── prj.conf                    # Zephyr 项目配置
└── build/                      # 构建输出
    ├── stloop_zephyr_compat.elf    # 固件
    ├── stloop_zephyr_compat.bin    # 二进制
    ├── stloop_zephyr_compat.hex    # Intel HEX
    └── simulation.resc             # Renode 脚本
```

## 故障排除

### 1. Zephyr 环境未找到

**错误**: `未找到 Zephyr SDK (ZEPHYR_BASE)`

**解决**:
```bash
# 设置 Zephyr 基础路径
$env:ZEPHYR_BASE = "E:\zephyr-workspace\zephyr"
```

### 2. Renode 未找到

**错误**: `未找到 Renode`

**解决**:
```bash
# 添加 Renode 到 PATH
$env:PATH += ";F:\Renode\bin"

# 或设置环境变量
$env:RENODE_BIN = "F:\Renode\bin\Renode.exe"
```

### 3. 构建失败 - 缺少 cmsis_minimal

**错误**: `找不到 cmsis_minimal`

**解决**:
```bash
# 从 cube 目录生成 cmsis_minimal
python -c "
from stloop.cube_manager import CubeManager
manager = CubeManager('E:\\bitloop_embedderdev-kind\\cube\\STM32CubeF4')
manager.copy_cmsis_minimal('E:\\bitloop_embedderdev-kind\\generated\\cmsis_minimal')
"
```

### 4. Unicode 编码错误

**现象**: 控制台显示乱码

**解决**:
```powershell
# 设置 UTF-8 编码
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
```

## 支持的 MCU

| MCU | Renode 平台文件 | 状态 |
|-----|----------------|------|
| STM32F411RE | platforms/cpus/stm32f4.repl | ✅ 已测试 |
| STM32F407VG | platforms/cpus/stm32f4.repl | ✅ 支持 |
| STM32F405RG | platforms/cpus/stm32f4.repl | ✅ 支持 |
| STM32F446RE | platforms/cpus/stm32f4.repl | ✅ 支持 |

## 高级用法

### 自定义 Renode 配置

```python
from stloop.simulators.renode import RenodeConfig, RenodeSimulator

config = RenodeConfig(
    mcu="STM32F411RE",
    gdb_port=3333,              # GDB 调试端口
    telnet_port=1234,           # Telnet 端口
    pause_on_startup=False,     # 启动时暂停
    show_gui=True,              # 显示 GUI
    enable_uart=True            # 启用 UART
)

sim = RenodeSimulator()
sim.start(elf_path, mcu="STM32F411RE", config=config, blocking=False)

# ... 运行一段时间后 ...
sim.stop()
```

### 批量构建和测试

```bash
# 构建多个项目
for dir in project1 project2 project3; do
    stloop build $dir --board nucleo_f411re
done

# 运行所有 Renode 测试
for resc in */build/*.resc; do
    echo "测试: $resc"
    timeout 10 renode --console "$resc" || echo "超时或失败"
done
```

## 参考

- [Zephyr 官方文档](https://docs.zephyrproject.org/)
- [Renode 文档](https://renode.readthedocs.io/)
- [STLoop README](../README.md)

## 更新日志

- **2025-03-18**: 修复 stloop builder.py zephyr_base 变量未定义问题
- **2025-03-18**: 添加端到端测试脚本
- **2025-03-18**: 完善文档
