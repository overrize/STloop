# STLoop Zephyr-Only Redesign

## 架构变更概览

### 删除的组件
- ✅ Cube LL 模板 (`templates/stm32_ll/`)
- ✅ CMSIS Minimal 模板 (`templates/cmsis_minimal/`)
- ✅ STM32Cube 下载脚本
- ✅ 芯片配置推断 (`chip_config.py`)
- ✅ 链接器脚本生成器 (`linker_gen.py`)

### 保留的核心功能
- LLM 代码生成 (改为生成 Zephyr 代码)
- West 构建系统封装
- West 烧录封装
- Renode 仿真

### 新增组件
- Zephyr Project Generator
- Board 数据库 (替代 MCU 数据库)
- Tauri 桌面 UI

## Board 映射表

| 原 Cube MCU | Zephyr Board | 状态 |
|-------------|--------------|------|
| STM32F411RE | nucleo_f411re | ✅ 支持 |
| STM32F401RE | nucleo_f401re | ✅ 支持 |
| STM32F446RE | nucleo_f446re | ✅ 支持 |
| STM32F407VG | stm32f4_disco | ✅ 支持 |
| STM32F429ZI | nucleo_f429zi | ✅ 支持 |

## 新工作流程

```
用户输入需求
    ↓
LLM 生成 Zephyr 代码
    ↓
生成 prj.conf (Kconfig)
    ↓
west build -b <board>
    ↓
west flash (或 Renode 仿真)
```

## 技术栈

- **RTOS**: Zephyr
- **构建**: West
- **桌面 UI**: Tauri + React
- **LLM**: OpenAI API (Kimi/OpenAI)
