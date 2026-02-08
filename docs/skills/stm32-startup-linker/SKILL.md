---
name: stm32-startup-linker
description: 处理 STM32 启动文件与链接脚本时使用。参考 CubeMX 机制，确保 GCC 工具链与 gcc/ 模板匹配。
---

# STM32 启动文件与链接脚本适配

参考：STM32CubeMX 链接脚本与启动文件机制详解

## 核心原则

**不同编译器的启动文件不能混用。** STLoop 使用 arm-none-eabi-gcc，必须使用 `gcc/` 目录下的 GNU 汇编语法启动文件。

## 一、模板路径

STM32Cube 固件包中的存储结构：

```
STM32Cube_FW_F4/Drivers/CMSIS/Device/ST/STM32F4xx/Source/Templates/
├── arm/    # ARMCC (MDK) — 不能用于 GCC
├── gcc/    # GNU 汇编 — STLoop 必须用此目录
└── iar/    # IAR — 不能用于 GCC
```

**实现时：** 复制或查找 startup 时，优先 `gcc/`，排除 `arm/`。

## 二、语法差异速查

| 特性 | GCC (arm-none-eabi) | MDK (arm/) |
|------|---------------------|------------|
| 语法 | GNU 汇编 | ARM 汇编 |
| CPU | `.cpu cortex-m4` | `PRESERVE8` / `THUMB` |
| 段 | `.section .text.Reset_Handler` | `AREA RESET, DATA` |
| 导出 | `.global g_pfnVectors` | `EXPORT __Vectors` |
| 数据 | `.word _sidata` | `DCD __initial_sp` |
| 弱引用 | `.weak Default_Handler` | `WEAK` |

## 三、链接脚本与启动文件的符号耦合

以下符号必须严格匹配，否则导致启动失败或数据错误：

| 链接脚本定义 | 启动文件引用 | 用途 |
|-------------|-------------|------|
| `_estack` | `ldr sp, =_estack` | 栈顶初始化 |
| `_sidata` | `.word _sidata` | .data 在 Flash 中的加载地址 |
| `_sdata` / `_edata` | `ldr r0, =_sdata` | .data 在 RAM 中的范围 |
| `_sbss` / `_ebss` | `ldr r1, =_sbss` | .bss 清零范围 |

**自生成 linker 或 startup 时**：必须保证符号名、段名与 GCC 模板一致。

## 四、STLoop 适配检查清单

1. **工具链检测**：使用前确认 `arm-none-eabi-gcc` 在 PATH
2. **startup 来源**：从 cube 的 `Source/Templates/gcc/` 复制，或使用等价 GNU 语法模板
3. **linker 来源**：cube 的 `Projects/.../[IDE]/.../*_FLASH.ld`，或自生成时参考 GCC 格式
4. **芯片内存**：FLASH/RAM/CCMRAM 需与具体型号一致（参见 chip_config / linker_gen）

## 五、常见问题

| 现象 | 可能原因 | 处理 |
|------|----------|------|
| 汇编报错 / 语法错误 | 用了 arm/ 的 Keil 语法 | 改用 gcc/ 下启动文件 |
| undefined reference _estack | linker 未定义或符号名不一致 | 检查 .ld 中 `_estack` 定义 |
| 全局变量初始化错 | .data 段复制失败 | 检查 _sidata/_sdata/_edata |
| 未初始化变量非零 | .bss 清零失败 | 检查 _sbss/_ebss 与 Reset_Handler 逻辑 |
| HardFault | 栈溢出或符号错误 | 调整 _Min_Stack_Size，核对 _estack |

## 六、GCC 11+ 兼容

若链接脚本含 `READONLY` 且 GCC 10 及以下报错，删除该关键字或升级工具链。
