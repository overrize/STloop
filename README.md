# STLoop v0.2.0 - Zephyr RTOS Edition

自然语言驱动 Zephyr RTOS 固件开发。描述需求 → AI 生成代码 → 自动构建 → 烧录/仿真。

## 🚀 快速开始

### 1. 安装依赖

```bash
# 安装 Zephyr SDK
# https://docs.zephyrproject.org/latest/develop/getting_started/index.html

# 安装 west 工具
pip install west

# 克隆项目
git clone https://github.com/yourusername/stloop.git
cd stloop
git checkout zephyr-only-redesign

# 安装 Python 包
pip install -e .
```

### 2. 配置环境变量

```bash
# Linux/Mac
export ZEPHYR_BASE=~/zephyrproject/zephyr
export OPENAI_API_KEY=your-api-key

# Windows
set ZEPHYR_BASE=C:\zephyrproject\zephyr
set OPENAI_API_KEY=your-api-key
```

### 3. 使用

```bash
# 生成项目
stloop generate "PA5 LED 每秒闪烁一次" --board nucleo_f411re

# 构建
cd stloop_projects/project_name
west build -b nucleo_f411re

# 烧录
west flash
```

## 📦 三种使用方式

### 方式一：命令行 (推荐)

```bash
# 交互模式
stloop chat

# 直接生成
stloop generate "描述你的需求" --board nucleo_f411re

# 查看支持的 boards
stloop boards
```

### 方式二：桌面应用 (Tauri)

```bash
cd stloop-ui
npm install
npm run tauri:dev    # 开发模式
npm run tauri:build  # 构建
```

### 方式三：Web 版本 (纯浏览器)

```bash
cd stloop-web
npm install
npm run dev      # 开发服务器
npm run build    # 构建到 dist/
```

## ✨ 特性

- 🤖 **AI 代码生成** - 自然语言 → Zephyr C 代码
- 🎯 **多 Board 支持** - Nucleo F411RE/F401RE/F446RE, Discovery
- 🔨 **一键构建** - 集成 west build
- ⚡ **一键烧录** - 集成 west flash
- 🖥️ **桌面应用** - Tauri 跨平台 (Windows/Mac/Linux)
- 🌐 **Web 版本** - 无需安装，浏览器即用
- 📦 **ZIP 导出** - 下载到本地构建

## 📋 支持的 Boards

| Board | MCU | 状态 |
|-------|-----|------|
| nucleo_f411re | STM32F411RE | ✅ |
| nucleo_f401re | STM32F401RE | ✅ |
| nucleo_f446re | STM32F446RE | ✅ |
| stm32f4_disco | STM32F407VG | ✅ |

## 🏗️ 架构

```
STLoop
├── stloop/           # Python 核心
│   ├── llm_client.py      # LLM 代码生成
│   ├── project_generator.py  # 项目生成
│   ├── builder.py         # west 封装
│   └── hardware/          # Board 数据库
├── stloop-ui/        # Tauri 桌面应用
│   ├── src-tauri/    # Rust 后端
│   └── src/          # React 前端
├── stloop-web/       # Web 版本
│   └── src/          # React 前端
└── templates/
    └── zephyr/       # Zephyr 模板
```

## 📖 文档

- [用户指南](docs/USER_GUIDE.md) - 详细使用说明
- [开发文档](docs/DEVELOPMENT.md) - 贡献者指南
- [架构设计](ARCHITECTURE.md) - 架构说明
- [API 文档](docs/API.md) - API 参考

## 🎯 工作流程

```
用户输入 → LLM 生成代码 → west build → west flash
```

## 🔧 系统要求

- Python 3.10+
- Zephyr SDK
- west 工具
- (可选) Node.js 18+ (桌面/Web 开发)
- (可选) Rust (桌面开发)

## 🤝 贡献

欢迎 PR 和 Issue！

## 📄 许可证

MIT License

## 🙏 致谢

- [Zephyr Project](https://zephyrproject.org/)
- [OpenAI](https://openai.com/) / [Kimi](https://moonshot.cn/)
- [Tauri](https://tauri.app/)
