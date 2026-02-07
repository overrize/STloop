# STLoop 使用指南

## 一、环境准备

### 1. 工具链

| 工具 | 说明 | 安装 |
|-----|------|------|
| arm-none-eabi-gcc | ARM 交叉编译器 | [GNU Arm](https://developer.arm.com/downloads/-/gnu-rm) |
| CMake | 构建系统 | [cmake.org](https://cmake.org/) |
| Python 3.10+ | 编排脚本 | - |
| pyOCD | 烧录与调试 | `pip install pyocd` |
| ST-Link | 调试器 | 连接 Nucleo 板载或外接 |

### 2. 硬件

- **推荐**：Nucleo-F411RE（板载 ST-Link，PA5 接 LED）
- 其他 STM32F4 板子需自行接线，并确保调试器可用

### 3. 项目依赖

```bash
cd stloop
pip install -r requirements.txt
```

## 二、Demo 场景：LED 闪烁

### 仅编译

```bash
stloop demo blink
# 或
python main.py demo blink
```

首次运行会自动下载 STM32CubeF4（约 100MB）。

### 编译 + 烧录

```bash
stloop demo blink --flash
```

连接 Nucleo-F411RE，板载 LED（PA5）应开始闪烁。

### 编译 + 烧录 + 自动化测试

```bash
stloop demo blink --flash --test
```

## 三、自然语言生成工程

需要配置 `OPENAI_API_KEY`：

```bash
# Linux/macOS
export OPENAI_API_KEY=sk-xxx

# 或使用 .env 文件
echo OPENAI_API_KEY=sk-xxx > .env
```

生成并编译、烧录：

```bash
stloop gen "PA5 控制 LED 闪烁" -o output/led --build --flash
```

## 四、配置说明

复制 `config/config.example.yaml` 为 `config/config.yaml`，可修改：

- `cube_path`：已有 STM32Cube 时的路径，留空则自动下载
- `target.chip`：目标芯片
- `llm.model`：大模型
- `pyocd.frequency`：调试频率

## 五、扩展

- 支持更多 Demo：在 `demos/` 下新增目录，参考 `blink`
- 支持更多芯片：修改 `templates/stm32_ll/CMakeLists.txt` 中的 MCU 相关配置
- 原理图/手册解析：后续版本将支持上传 PDF，由 LLM 提取管脚与需求
