# STLoop 中的 Cube vs Zephyr：设计选择说明

## 为什么默认使用 STM32Cube？

### 1. 设计初衷

STLoop 最初设计为 **STM32 专用工具**，核心目标是：
- **简单直接**：用户只需要安装 ARM GCC 即可开始开发
- **最小依赖**：不需要复杂的 Zephyr SDK 环境
- **与 ST 生态无缝集成**：使用官方 STM32Cube HAL/LL 库

### 2. Cube 模式的优势

| 优势 | 说明 |
|------|------|
| **即装即用** | 只需要 `arm-none-eabi-gcc` 和 `cmake` |
| **官方支持** | 直接来自 ST 的 HAL/LL 驱动，文档齐全 |
| **代码直观** | 寄存器级操作，易于理解和调试 |
| **体积小巧** | 生成的固件体积小，启动快 |
| **学习曲线平缓** | 适合嵌入式初学者 |

### 3. Zephyr 已支持但需显式启用

STLoop **已经支持 Zephyr**，但需要用户显式选择，因为：
- Zephyr 需要额外的环境配置（ZEPHYR_BASE, west 工具链）
- Zephyr 学习曲线较陡（Device Tree, Kconfig 等概念）
- 不是所有用户都需要 RTOS 功能

## 两种模式对比

| 特性 | Cube 模式 (默认) | Zephyr 模式 |
|------|-----------------|-------------|
| **底层实现** | STM32Cube HAL/LL | Zephyr RTOS + 设备树 |
| **依赖** | ARM GCC + CMake | ARM GCC + Zephyr SDK + west |
| **模板位置** | `templates/stm32_ll/` | `templates/zephyr/` |
| **项目标志** | 无特殊标志 | `prj.conf` + 特殊 CMakeLists.txt |
| **代码风格** | 寄存器直接操作 | Zephyr API (gpio_dt_spec 等) |
| **多平台** | ❌ 仅 STM32 | ✅ STM32, nRF, ESP32 等 |
| **RTOS 功能** | ❌ 裸机 | ✅ 内置多任务、调度器 |
| **生态丰富度** | 中等 | 非常丰富（网络、蓝牙等） |

## 如何选择？

### 使用 Cube 模式（默认）如果：
- ✅ 只需要简单的 GPIO、UART、定时器操作
- ✅ 希望快速上手，不想配置复杂环境
- ✅ 学习嵌入式编程基础
- ✅ 对固件大小和启动速度有严格要求
- ✅ 只针对 STM32 平台

### 使用 Zephyr 模式如果：
- ✅ 需要多任务、实时调度
- ✅ 项目可能跨平台（STM32 → nRF52）
- ✅ 需要丰富的协议栈（BLE、WiFi、MQTT）
- ✅ 团队已熟悉 Zephyr 生态
- ✅ 需要现代化的开发体验

## 快速切换指南

### 方法 1：手动转换项目

如果你已经用 `stloop gen` 生成了 Cube 项目，可以手动转换为 Zephyr：

```bash
cd generated

# 1. 替换 CMakeLists.txt
cat > CMakeLists.txt << 'EOF'
cmake_minimum_required(VERSION 3.20.0)
find_package(Zephyr REQUIRED HINTS $ENV{ZEPHYR_BASE})
project(my_app)
target_sources(app PRIVATE src/main.c)
EOF

# 2. 创建 prj.conf
cat > prj.conf << 'EOF'
CONFIG_CONSOLE=y
CONFIG_UART_CONSOLE=y
CONFIG_SERIAL=y
CONFIG_GPIO=y
CONFIG_SYS_CLOCK_HW_CYCLES_PER_SEC=100000000
EOF

# 3. 修改 main.c 为 Zephyr API（见下文示例）

# 4. 删除 Cube 相关文件
rm -rf cube/
rm -f *.ld startup_*.s
```

### 方法 2：使用现有 Zephyr 模板

```bash
# 直接复制 Zephyr 模板
cp -r templates/zephyr my_zephyr_project

# 修改 src/main.c 为你的代码
# 然后构建
cd my_zephyr_project
west build -b nucleo_f411re .
```

### 方法 3：Python API 强制使用 Zephyr

```python
from stloop import STLoopClient
from pathlib import Path

client = STLoopClient()

# 生成项目（当前仍使用 Cube 模板）
client.gen("PA5 LED blink", output_dir="my_project")

# 构建时强制使用 Zephyr
elf = client.build(
    "my_project", 
    use_zephyr=True  # 强制使用 Zephyr 构建
)
```

**注意**：这种方式需要项目已经是 Zephyr 项目格式（有 `prj.conf` 和正确的 `CMakeLists.txt`）

## 代码示例对比

### Cube 模式（寄存器直接操作）

```c
#include "stm32f4xx_ll_gpio.h"
#include "stm32f4xx_ll_bus.h"

int main(void) {
    // 使能 GPIOA 时钟
    LL_AHB1_GRP1_EnableClock(LL_AHB1_GRP1_PERIPH_GPIOA);
    
    // 配置 PA5 为输出
    LL_GPIO_SetPinMode(GPIOA, LL_GPIO_PIN_5, LL_GPIO_MODE_OUTPUT);
    
    while (1) {
        LL_GPIO_TogglePin(GPIOA, LL_GPIO_PIN_5);
        LL_mDelay(500);
    }
}
```

### Zephyr 模式（设备树 + API）

```c
#include <zephyr/kernel.h>
#include <zephyr/drivers/gpio.h>

// 设备树获取 LED 定义
static const struct gpio_dt_spec led = GPIO_DT_SPEC_GET(DT_ALIAS(led0), gpios);

void main(void) {
    // 配置 GPIO
    gpio_pin_configure_dt(&led, GPIO_OUTPUT_ACTIVE);
    
    while (1) {
        gpio_pin_toggle_dt(&led);
        k_msleep(500);
    }
}
```

## 未来计划

为了让用户更方便地选择，我们计划：

1. **添加 `--zephyr` 标志**：`stloop gen "LED blink" --zephyr`
2. **自动检测**：如果检测到 `ZEPHYR_BASE` 环境变量，询问是否使用 Zephyr
3. **混合模式**：允许在 Cube 项目中逐步引入 Zephyr 子系统

## 总结

- **默认 Cube**：简单、轻量、快速上手
- **可选 Zephyr**：功能丰富、跨平台、现代化
- **两者并存**：根据项目需求选择
- **手动转换**：当前需要手动切换，未来会更方便

**选择建议**：
- 初学者 → 使用 Cube 模式
- 需要 RTOS → 使用 Zephyr 模式
- 不确定 → 先用 Cube，需要时再迁移
