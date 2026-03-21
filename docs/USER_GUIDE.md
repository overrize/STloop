# STLoop 用户指南

## 目录
1. [安装](#安装)
2. [快速开始](#快速开始)
3. [CLI 使用](#cli-使用)
4. [桌面应用](#桌面应用)
5. [Web 版本](#web-版本)
6. [常见问题](#常见问题)

## 安装

### 前提条件

1. **Python 3.10+**
2. **Zephyr SDK** - [安装指南](https://docs.zephyrproject.org/latest/develop/getting_started/index.html)
3. **west 工具** - `pip install west`
4. **API Key** - OpenAI 或 Kimi(Moonshot)

### 安装步骤

```bash
# 克隆仓库
git clone https://github.com/yourusername/stloop.git
cd stloop
git checkout zephyr-only-redesign

# 安装 Python 依赖
pip install -e .

# 验证安装
stloop --version
```

### 环境配置

创建 `.env` 文件：

```bash
# OpenAI
OPENAI_API_KEY=sk-your-key

# 或 Kimi (推荐国内用户)
OPENAI_API_KEY=sk-your-key
OPENAI_API_BASE=https://api.moonshot.cn/v1
OPENAI_MODEL=kimi-k2-0905-preview
```

## 快速开始

### 1. 生成 LED 闪烁代码

```bash
stloop generate "PA5 LED 每秒闪烁一次" --board nucleo_f411re
```

### 2. 构建项目

```bash
cd stloop_projects/project_name
west build -b nucleo_f411re
```

### 3. 烧录到设备

```bash
west flash
```

## CLI 使用

### 命令列表

```bash
# 查看帮助
stloop --help

# 交互式聊天
stloop chat

# 生成项目
stloop generate "描述" --board nucleo_f411re

# 查看支持的 boards
stloop boards

# 查看项目列表
stloop list

# 删除项目
stloop delete <project-id>
```

### generate 命令

```bash
stloop generate "需求描述" [选项]

选项：
  --board BOARD    目标 board (默认: nucleo_f411re)
  --output DIR     输出目录 (默认: ./stloop_projects/)
  --name NAME      项目名称

示例：
  stloop generate "UART1 发送 Hello World" --board nucleo_f446re
  stloop generate "ADC 读取 PA0" --board nucleo_f411re --name adc_demo
```

### 支持的描述格式

STLoop 可以理解自然语言描述：

```bash
# GPIO
"PA5 LED 闪烁"
"PC13 按键中断"

# UART
"UART1 发送 Hello World"
"UART2 接收数据"

# I2C
"I2C1 读取传感器"

# PWM
"PA0 PWM 输出 1kHz"

# ADC
"ADC 读取 PA0"

# 组合功能
"读取 ADC 并通过 UART 发送"
```

## 桌面应用

### 启动

```bash
cd stloop-ui
npm install
npm run tauri:dev
```

### 使用界面

1. **选择 Board** - 下拉选择目标板
2. **输入需求** - 描述想要的功能
3. **点击发送** - AI 生成代码
4. **查看代码** - 在右侧编辑器查看
5. **点击构建** - 运行 west build
6. **点击烧录** - 运行 west flash

### 快捷键

- `Ctrl+Enter` - 发送消息
- `Ctrl+Shift+Enter` - 换行
- `Ctrl+B` - 构建
- `Ctrl+F` - 烧录

## Web 版本

### 访问

```bash
cd stloop-web
npm install
npm run dev
# 打开 http://localhost:3000
```

### 功能

Web 版本提供：
- ✅ AI 代码生成
- ✅ 项目查看
- ✅ ZIP 导出
- ❌ 直接构建 (需要下载后用 west)

### 使用流程

1. 输入需求并选择 Board
2. 点击生成
3. 查看生成的代码
4. 点击「导出 ZIP」
5. 解压 ZIP
6. 运行 `west build -b nucleo_f411re`

## 项目结构

生成的项目结构：

```
project_name/
├── CMakeLists.txt    # Zephyr CMake 配置
├── prj.conf         # 项目配置 (Kconfig)
└── src/
    └── main.c       # 生成的代码
```

## 自定义配置

### prj.conf

启用额外功能：

```conf
# 启用串口
CONFIG_UART_INTERRUPT_DRIVEN=y

# 启用 I2C
CONFIG_I2C=y

# 启用 SPI
CONFIG_SPI=y

# 启用 PWM
CONFIG_PWM=y

# 启用 ADC
CONFIG_ADC=y
```

### 修改生成的代码

生成的代码位于 `src/main.c`，可以直接编辑后重新构建：

```bash
west build
```

## 故障排除

### west 命令未找到

```bash
pip install west
```

### ZEPHYR_BASE 未设置

```bash
# Linux/Mac
export ZEPHYR_BASE=~/zephyrproject/zephyr

# Windows
set ZEPHYR_BASE=C:\zephyrproject\zephyr
```

### 构建失败

1. 检查 board 名称是否正确
2. 检查 Zephyr SDK 是否安装
3. 检查项目配置是否正确

### API 错误

检查 `.env` 文件中的 API key 是否正确设置。

## 示例

### LED 闪烁

```bash
stloop generate "PA5 LED 每秒闪烁一次"
cd stloop_projects/*/ && west build -b nucleo_f411re && west flash
```

### UART 发送

```bash
stloop generate "UART2 发送 Hello World 每秒一次"
cd stloop_projects/*/ && west build -b nucleo_f411re
```

### ADC 读取

```bash
stloop generate "ADC1 读取 PA0 并通过 UART 发送"
cd stloop_projects/*/ && west build -b nucleo_f411re
```

## 提示

1. **描述越详细，代码质量越高**
2. **使用具体的引脚名称** (如 PA5 而不是 "LED 引脚")
3. **明确指定功能** (如 "每秒闪烁" 而不是 "闪烁")
4. **Web 版本适合快速原型**，桌面/CLI 适合完整开发
