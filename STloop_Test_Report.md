# STLoop 功能测试报告

**测试日期**: 2026-02-09  
**测试环境**: Windows (cmd)  
**测试人员**: QA  

---

## 测试概览

| 测试项 | 状态 | 备注 |
|--------|------|------|
| CLI 版本查询 | ✅ 通过 | 版本 0.1.0 |
| 环境检查 | ✅ 通过 | 工具链和 Cube 就绪 |
| 帮助信息 | ✅ 通过 | 所有命令帮助正常 |
| Demo Blink (仅编译) | ❌ 失败 | 缺少 linker script |
| Demo Blink (烧录) | ⏭️ 跳过 | 依赖编译成功 |
| 工程生成 | 🔄 进行中 | - |
| 编译功能 | 🔄 进行中 | - |

---

## 详细测试结果

### 1. CLI 版本查询
**命令**: `python -m stloop --version`  
**状态**: ✅ 通过  
**输出**:
```
stloop 0.1.0
```
**结论**: 版本信息正常显示

---

### 2. 环境检查
**命令**: `python -m stloop check`  
**状态**: ✅ 通过  
**输出**:
```
[stloop] INFO: 工具链: E:\arm_nobi\bin\arm-none-eabi-gcc.EXE
arm-none-eabi-gcc: 已就绪
[stloop] INFO: 检查 STM32CubeF4: E:\stloop_test\STloop\cube\STM32CubeF4
[stloop] INFO: cube 目录已有芯片库，跳过下载: E:\stloop_test\cube\STM32CubeF4-1.28.3
STM32CubeF4: 已就绪 (E:\stloop_test\cube\STM32CubeF4-1.28.3)
环境检查通过
```
**结论**: 
- arm-none-eabi-gcc 工具链已就绪
- STM32CubeF4 库已存在并可用
- 环境配置正确

---

### 3. 帮助信息
**命令**: `python -m stloop --help`  
**状态**: ✅ 通过  
**输出**: 显示所有可用命令：chat, demo, gen, cube-download, check, build  
**结论**: CLI 帮助系统正常工作

**命令**: `python -m stloop demo --help`  
**状态**: ✅ 通过  
**输出**: 显示 demo 子命令选项（blink, --flash, --test）  
**结论**: 子命令帮助正常

---

### 4. Demo Blink (仅编译)
**命令**: `python -m stloop demo blink`  
**状态**: ❌ 失败  
**错误信息**:
```
CMake Error at CMakeLists.txt:155 (message):
  No linker script .ld in project dir or under
  E:/stloop_test/cube/STM32CubeF4-1.28.3 (checked CMSIS, Drivers, Projects)
```
**详细日志**:
- 模板文件成功复制到 demos/blink
- CMake 配置阶段失败
- 编译器识别正常 (GNU 8.1.0)
- 缺少 linker script (.ld 文件)

**问题分析**:
1. CMakeLists.txt 在工程目录和 Cube 库中都找不到 .ld 文件
2. 检查路径：CMSIS, Drivers, Projects
3. 可能原因：Cube 库不完整或 linker script 位置不正确

**结论**: 编译失败，需要修复 linker script 问题

---


### 5. Gen 命令帮助
**命令**: `python -m stloop gen --help`  
**状态**: ✅ 通过  
**输出**: 显示 gen 命令的所有选项（prompt, -o, --build, --flash）  
**结论**: 帮助信息完整

---

### 6. Build 命令帮助
**命令**: `python -m stloop build --help`  
**状态**: ✅ 通过  
**输出**: 显示 build 命令选项（project, --flash）  
**结论**: 帮助信息正常

---

### 7. Gen 命令 (仅生成，不编译)
**命令**: `python -m stloop gen "PA5 控制 LED 闪烁" -o test_output/led_test`  
**状态**: ✅ 通过  
**输出**:
```
[stloop] INFO: 推断芯片: MCU_DEVICE=STM32F411xE
  [生成] 推断芯片: STM32F411xE
  [生成] 使用模型: kimi-k2-0905-preview
  [生成] 正在调用 API...
  [生成] 收到响应 (1257 字符)
  [生成] 解析代码块完成，输出 43 行
  [生成] 写入 main.c...
  [生成] 复制工程模板...
工程已生成: E:\stloop_test\STloop\test_output\led_test
```
**生成的文件**:
- chip_config.cmake
- CMakeLists.txt
- src/main.c (43 行，包含 LL 库代码)
- inc/main.h
- inc/stm32f4xx_hal_conf.h

**生成的代码质量**:
- ✅ 正确使用 STM32 LL 库
- ✅ 包含 SystemClock_Config 函数
- ✅ GPIO 配置正确（PA5, 输出模式）
- ✅ LED 闪烁逻辑正确（500ms 延时）
- ✅ 代码结构清晰

**结论**: 
- LLM 代码生成功能正常
- 芯片推断准确（STM32F411xE）
- 生成的代码符合 LL 库规范
- 警告：未内嵌 cube，跳过复制 .ld/startup（预期行为）

---

### 8. Python 单元测试
**命令**: `python -m pytest tests/ -v`  
**状态**: ⚠️ 部分通过  
**结果**: 10 passed, 1 failed  

**通过的测试**:
1. ✅ test_get_projects_dir_inside_stloop
2. ✅ test_get_projects_dir_outside_stloop
3. ✅ test_import_stloop
4. ✅ test_client_init
5. ✅ test_cli_version
6. ✅ test_llm_config
7. ✅ test_chat_exits_when_not_configured
8. ✅ test_chip_config_infer
9. ✅ test_gen_raises_without_api_key
10. ✅ test_gen_writes_chip_config

**失败的测试**:
- ❌ test_embed_cube_skips_when_already_embedded
  - 错误类型: RecursionError (递归深度超限)
  - 错误位置: shutil.copytree 在 _embed_cube 方法中
  - 问题分析: 复制 cube 目录时出现递归复制问题

**结论**: 
- 核心功能测试通过
- _embed_cube 方法存在递归复制 bug

---

## 测试总结

### 通过的功能 ✅
1. CLI 版本查询
2. 环境检查（工具链和 Cube 库）
3. 所有命令的帮助信息
4. 自然语言代码生成（gen 命令）
5. LLM API 集成
6. 芯片推断功能
7. 大部分单元测试

### 失败的功能 ❌
1. Demo Blink 编译 - 缺少 linker script (.ld 文件)
2. _embed_cube 方法 - 递归复制问题

### 未测试的功能 ⏭️
1. 烧录功能（--flash）- 需要硬件连接
2. 自动化测试（--test）- 需要硬件连接
3. 交互式 chat 模式
4. Build 命令（依赖 linker script 问题修复）

### 关键问题
1. **Linker Script 缺失**: CMakeLists.txt 无法在 Cube 库中找到 .ld 文件
2. **递归复制 Bug**: _embed_cube 方法在复制 cube 目录时出现无限递归

### 建议
1. 修复 linker script 查找逻辑或提供默认 .ld 文件
2. 修复 _embed_cube 的递归复制问题
3. 添加硬件连接后测试烧录和测试功能

---

**测试完成时间**: 2026-02-09 23:30


---

## 真实场景测试计划

### 测试场景描述
**项目**: STM32F405 IMU 模块验证  
**需求**: 验证读取的 BMI088 传感器数据是否正确  
**芯片**: STM32F405RGT6  
**传感器**: BMI088 (6轴 IMU)  

### 可用文档
1. ✅ MCU 原理图: `E:\BaiduNetdiskDownload\IMU V1.2\MCU.pdf`
2. ✅ 芯片手册: `C:\Users\51771\Downloads\stm32f405rgt6.pdf`
3. ✅ 传感器手册: `C:\Users\51771\Downloads\bmi088.pdf`

### 环境检查结果
- ✅ arm-none-eabi-gcc: 已就绪 (E:\arm_nobi\bin\arm-none-eabi-gcc.EXE)
- ✅ STM32CubeF4: 已就绪 (E:\stloop_test\cube\STM32CubeF4-1.28.3)
- ✅ 所有 PDF 文档存在

### 测试步骤

#### 第一步: 生成 IMU 读取代码
**命令**:
```bash
python -m stloop gen "我设计了一个 STM32F405 的 IMU 模块，帮我验证读取的传感器数据对不对" -o output/imu_test
```
**预期结果**:
- 推断芯片为 STM32F405xx
- 生成 BMI088 传感器初始化代码
- 生成 I2C/SPI 通信代码
- 生成数据读取和验证代码

#### 第二步: 生成并编译
**命令**:
```bash
python -m stloop gen "我设计了一个 STM32F405 的 IMU 模块，帮我验证读取的传感器数据对不对" -o output/imu_test --build
```
**预期结果**:
- 代码生成成功
- 编译通过，生成 .elf 文件
- 如果编译失败，自动修复最多 3 轮

#### 第三步: 生成、编译并烧录（需要硬件）
**命令**:
```bash
python -m stloop gen "我设计了一个 STM32F405 的 IMU 模块，帮我验证读取的传感器数据对不对" -o output/imu_test --build --flash
```
**预期结果**:
- 完整流程执行
- 固件烧录到 STM32F405
- 可通过串口查看传感器数据

### 测试关注点
1. **芯片推断**: 是否正确识别 STM32F405
2. **传感器识别**: 是否识别 BMI088
3. **通信协议**: I2C 或 SPI 配置是否正确
4. **代码质量**: 
   - 寄存器配置是否正确
   - 数据读取逻辑是否完整
   - 错误处理是否存在
5. **编译结果**: 是否能成功编译
6. **实际运行**: 传感器数据是否正确（需要硬件）

### 风险评估
- ⚠️ Linker script 问题可能导致编译失败
- ⚠️ PDF 解析功能可能未完全实现
- ⚠️ 复杂的传感器驱动可能需要多轮修复
- ⚠️ 没有硬件无法验证实际运行效果

---

## 开始真实场景测试


### 测试 9: 真实场景 - STM32F405 IMU 模块代码生成

**命令**: 
```bash
python -m stloop gen "我设计了一个 STM32F405 的 IMU 模块，帮我验证读取的传感器数据对不对" -o output/imu_test
```

**状态**: ✅ 代码生成成功

**输出信息**:
```
[stloop] INFO: 推断芯片: MCU_DEVICE=STM32F405xx
  [生成] 推断芯片: STM32F405xx
  [生成] 使用模型: kimi-k2-0905-preview
  [生成] 收到响应 (3650 字符)
  [生成] 解析代码块完成，输出 111 行
  [生成] 写入 main.c...
工程已生成: E:\stloop_test\STloop\output\imu_test
```

**生成的代码分析**:

#### 1. 芯片识别
- ✅ 正确识别为 STM32F405xx
- ✅ chip_config.cmake 配置正确
  - MCU_DEVICE: STM32F405xx
  - STARTUP_PATTERN: f405
  - LINKER_PATTERN: F405

#### 2. 传感器识别
- ⚠️ **问题**: LLM 生成的是 MPU6500 代码，而不是 BMI088
- 原因分析: 
  - 可能 PDF 解析功能未启用
  - 或者 LLM 基于通用 IMU 模式生成代码
  - BMI088 是较新的传感器，LLM 可能默认使用更常见的 MPU6500

#### 3. 代码质量评估

**优点** ✅:
1. **SPI 配置完整**:
   - GPIO 配置正确（PA4-CS, PA5-SCK, PA6-MISO, PA7-MOSI）
   - SPI1 初始化完整
   - 时钟配置正确
   - 主从模式、极性、相位设置合理

2. **寄存器操作规范**:
   - 读写函数实现正确
   - CS 片选控制正确
   - 读操作使用 0x80 标志位
   - 写操作使用 0x7F 掩码

3. **初始化流程合理**:
   - 软复位 (PWR_MGMT_1 = 0x80)
   - 延时 100ms
   - 配置采样率、滤波器、量程

4. **数据读取逻辑**:
   - 连续读取 14 字节（加速度 6 + 温度 2 + 陀螺仪 6）
   - 正确组合高低字节
   - 数据类型使用 int16_t

5. **错误检测**:
   - WHO_AM_I 寄存器验证
   - 验证失败进入死循环

**缺点** ⚠️:
1. **传感器型号错误**: 应该是 BMI088，生成的是 MPU6500
2. **缺少串口输出**: 只有 TODO 注释，无法直接查看数据
3. **时钟配置简化**: `LL_SetSystemCoreClock(100000000)` 不是标准 LL 库函数
4. **缺少详细注释**: 寄存器地址和配置值缺少说明

#### 4. 代码结构
- ✅ 111 行代码，结构清晰
- ✅ 函数划分合理：初始化、读写、数据采集
- ✅ 使用 LL 库，符合项目要求
- ✅ 宏定义清晰，便于移植

**结论**:
- 代码生成功能正常工作
- 芯片推断准确
- 代码质量较高，可作为基础框架
- 需要手动修改为 BMI088 驱动（或提供更详细的传感器信息）

---

### 测试 10: 真实场景 - 编译 IMU 代码

**命令**: 
```bash
python -m stloop build output/imu_test
```

**状态**: ❌ 编译失败

**错误信息**:
```
CMake Error at CMakeLists.txt:155 (message):
  No linker script .ld in project dir or under
  E:/stloop_test/cube/STM32CubeF4-1.28.3 (checked CMSIS, Drivers, Projects)
```

**问题分析**:
- 与 Demo Blink 相同的 linker script 缺失问题
- CMakeLists.txt 无法在 Cube 库中找到 STM32F405 的 .ld 文件
- 阻止了所有编译测试

**影响**:
- 无法测试完整的 gen --build 流程
- 无法测试自动修复功能
- 无法生成可烧录的固件

---

## 真实场景测试总结

### 成功的部分 ✅
1. **自然语言理解**: 正确理解了 "STM32F405 IMU 模块" 的需求
2. **芯片推断**: 准确识别 STM32F405xx
3. **代码生成**: 生成了 111 行完整的 IMU 驱动代码
4. **SPI 驱动**: 生成的 SPI 配置和操作代码质量高
5. **项目结构**: 文件组织合理，符合 STM32 项目规范

### 存在的问题 ❌
1. **传感器识别**: 生成 MPU6500 而非 BMI088（可能 PDF 解析未启用）
2. **Linker Script**: 编译阶段失败，无法生成固件
3. **时钟配置**: 使用了非标准的 LL 库函数

### 未测试的功能 ⏭️
1. PDF 文档解析功能（原理图、芯片手册、传感器手册）
2. 自动编译修复功能（3 轮修复）
3. 烧录功能
4. 实际硬件验证

### 建议改进
1. **优先修复**: Linker script 问题，这是阻塞性问题
2. **PDF 解析**: 验证 PDF 解析功能是否启用，如何使用
3. **传感器库**: 扩展 LLM 对新型传感器（如 BMI088）的支持
4. **串口输出**: 默认生成包含串口调试输出的代码

---

**真实场景测试完成时间**: 2026-02-09 23:45


---

## 🔄 重新测试（2026-02-09 23:50）

### 重测环境验证
**命令**: `python -m stloop check`  
**状态**: ✅ 通过  
- arm-none-eabi-gcc: 已就绪
- STM32CubeF4: 已就绪
- 环境正常

---

### 重测 1: Demo Blink 编译

**命令**: `python -m stloop demo blink`  
**状态**: ❌ 失败（但有进展）

**✅ 已修复的问题**:
1. **Linker Script 自动生成** - 成功生成 STM32F411xx_FLASH.ld (512K Flash, 128K RAM)
2. **Startup 文件自动复制** - 成功从 Cube 库复制 startup_stm32f411xe.s

**❌ 新发现的问题**:

#### 问题 1: 模板 main.c 缺少头文件
**错误信息**:
```
error: implicit declaration of function 'LL_FLASH_SetLatency'
error: 'LL_FLASH_LATENCY_2' undeclared
error: implicit declaration of function 'LL_RCC_HSE_Enable'
error: implicit declaration of function 'LL_RCC_PLL_ConfigDomain_SYS'
```

**根本原因**: `demos/blink/src/main.c` 缺少必要的 LL 库头文件

**需要添加的头文件**:
```c
#include "stm32f4xx_ll_rcc.h"
#include "stm32f4xx_ll_flash.h"
#include "stm32f4xx_ll_system.h"
```

#### 问题 2: HAL 配置文件问题
**错误信息**:
```
error: unknown type name '__IO'
error: unknown type name 'uint32_t'
note: 'uint32_t' is defined in header '<stdint.h>'
```

**根本原因**: `inc/stm32f4xx_hal_conf.h` 配置不完整

**影响范围**: 所有使用模板的项目

---

### 重测 2: 简单 LED 代码生成

**命令**: `python -m stloop gen "PA5 控制 LED 闪烁" -o output/led_simple`  
**状态**: ✅ 成功

**生成结果**:
- 芯片推断: STM32F411xE ✅
- 代码行数: 41 行
- 响应时间: ~5 秒
- 代码质量: 优秀

**生成的代码特点**:
```c
// 包含了正确的头文件
#include "main.h"
#include "stm32f4xx_ll_gpio.h"
#include "stm32f4xx_ll_bus.h"
#include "stm32f4xx_ll_rcc.h"
#include "stm32f4xx_ll_utils.h"

// 完整的时钟配置
static void SystemClock_Config(void);
static void LED_Init(void);

// 清晰的主循环
int main(void) {
    SystemClock_Config();
    LED_Init();
    while (1) {
        LL_GPIO_TogglePin(GPIOA, LL_GPIO_PIN_5);
        LL_mDelay(500);
    }
}
```

**对比发现**: 
- ✅ LLM 生成的代码包含了正确的头文件
- ❌ 模板文件（demos/blink）缺少这些头文件
- **结论**: 模板需要更新以匹配 LLM 生成的代码质量

---

### 重测 3: 复杂场景 - IMU 模块

**命令**: `python -m stloop gen "我设计了一个 STM32F405 的 IMU 模块，帮我验证读取的传感器数据对不对" -o output/imu_v2 --build`  
**状态**: ⏸️ API 超时（180 秒）

**问题分析**:
- 复杂需求导致 LLM 响应时间过长
- 可能需要增加超时时间或简化 prompt

---

## 🔍 问题汇总与优先级

### 🔴 P0 - 阻塞性问题（必须立即修复）

#### 1. 模板文件头文件缺失
**文件**: `templates/stm32_ll/src/main.c`  
**问题**: 缺少 LL 库头文件导致编译失败  
**影响**: 所有使用模板的项目（demo blink）无法编译  
**修复方案**: 在模板 main.c 开头添加：
```c
#include "stm32f4xx_ll_rcc.h"
#include "stm32f4xx_ll_flash.h"
#include "stm32f4xx_ll_system.h"
```

#### 2. HAL 配置文件不完整
**文件**: `templates/stm32_ll/inc/stm32f4xx_hal_conf.h`  
**问题**: 缺少基础类型定义  
**影响**: HAL/LL 库编译失败  
**修复方案**: 确保正确包含 CMSIS 核心头文件

---

### 🟡 P1 - 重要问题（应尽快修复）

#### 3. API 超时问题
**场景**: 复杂需求（IMU 模块）  
**问题**: 180 秒超时  
**影响**: 无法生成复杂项目代码  
**修复方案**: 
- 增加超时时间到 300 秒
- 添加重试机制
- 或提供进度提示

#### 4. _embed_cube 递归复制 Bug
**位置**: `stloop/client.py::_embed_cube`  
**问题**: 单元测试失败，递归深度超限  
**影响**: 内嵌 cube 功能不可用  
**修复方案**: 检查复制逻辑，避免循环引用

---

### 🟢 P2 - 改进建议（可以后续优化）

#### 5. 传感器识别偏差
**问题**: 生成 MPU6500 而非 BMI088 代码  
**原因**: PDF 解析功能可能未启用  
**建议**: 验证并启用 PDF 文档解析功能

#### 6. 缺少串口调试输出
**问题**: 生成的代码只有 TODO 注释  
**建议**: 默认生成包含 UART 调试输出的代码

---

## ✅ 已修复的问题

1. ✅ **Linker Script 缺失** - 现在能自动生成
2. ✅ **Startup 文件缺失** - 现在能自动从 Cube 库复制

---

## 📊 功能完成度评估

| 功能模块 | 完成度 | 状态 | 备注 |
|---------|--------|------|------|
| 环境检查 | 100% | ✅ | 完全正常 |
| 代码生成 | 95% | ✅ | LLM 生成质量高 |
| 芯片推断 | 100% | ✅ | 准确识别 |
| Linker/Startup | 100% | ✅ | 已自动化 |
| 模板系统 | 60% | ❌ | 缺少头文件 |
| 编译系统 | 70% | ⚠️ | 模板问题导致失败 |
| 烧录功能 | - | ⏭️ | 需要硬件 |
| 测试功能 | - | ⏭️ | 需要硬件 |

---

## 🎯 开发者行动清单

### 立即修复（阻塞编译）
- [ ] 修复 `templates/stm32_ll/src/main.c` - 添加 LL 库头文件
- [ ] 修复 `templates/stm32_ll/inc/stm32f4xx_hal_conf.h` - 完善配置
- [ ] 验证修复：运行 `python -m stloop demo blink` 应该编译成功

### 尽快修复（影响体验）
- [ ] 增加 API 超时时间或添加重试机制
- [ ] 修复 `_embed_cube` 递归复制 bug
- [ ] 运行单元测试确保通过：`python -m pytest tests/ -v`

### 后续优化（提升质量）
- [ ] 验证 PDF 解析功能是否启用
- [ ] 为生成的代码添加默认串口调试输出
- [ ] 添加更多 demo 示例

---

**最后更新时间**: 2026-02-09 23:58  
**测试状态**: 发现关键问题，等待修复
