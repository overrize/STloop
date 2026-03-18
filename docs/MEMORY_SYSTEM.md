# STLoop 项目记忆系统

## 功能概述

STLoop 现在支持**项目记忆**功能，可以：

1. **记住项目信息** - 自动保存项目描述、MCU 型号、使用的功能
2. **持续对话** - 断开后可以重新进入，继续之前的上下文
3. **智能建议** - 根据项目状态推荐下一步操作
4. **任务队列** - 管理待办任务，追踪完成进度

## 快速开始

### 1. 首次使用（创建新项目）

```bash
python -m stloop

> 描述你的项目：STM32F411RE 开发板，PA5 LED 闪烁，每 500ms 切换一次

[系统] 发现相似的项目:
  1. STM32F411RE_LED_blink_20240318 (最后更新: 2024-03-18)
  2. Nucleo_F411RE_blink_20240315

> 输入编号继续已有项目，或按 Enter 创建新项目: [Enter]

[系统] 创建新会话: STM32F411RE_开发板_PA5_LED
[系统] Session ID: session_20240318_143022_abc123
```

### 2. 持续对话

```bash
# 继续之前的项目（自动加载最近会话）
python -m stloop --continue

# 或指定 Session ID
python -m stloop --session session_20240318_143022_abc123
```

### 3. 查看项目状态

```bash
# 查看当前项目信息
> status

项目: STM32F411RE_开发板_PA5_LED
描述: STM32F411RE 开发板，PA5 LED 闪烁，每 500ms 切换一次
状态: developing
MCU: STM32F411RE
框架: cube
已实现功能: LED blink, 500ms interval
使用外设: GPIO, TIM
待办任务: 2 个

建议下一步:
  1. 编译并仿真测试
  2. 添加串口输出调试信息
  3. 查看项目状态
```

### 4. 任务管理

```bash
# 查看任务列表
> tasks

待办任务:
  [ ] task_1: 编译并仿真测试
  [ ] task_2: 添加串口输出调试信息

已完成:
  [x] task_0: 生成 LED 闪烁代码
      结果: 已生成代码，使用 PA5 GPIO
      修改: src/main.c, inc/main.h

# 添加新任务
> add_task 优化功耗，使用低功耗模式

# 完成任务
> complete_task task_1 编译成功，固件大小 2.1KB
```

## Python API 使用

### 基础用法

```python
from stloop.memory import create_or_load_session, get_memory_manager

# 创建或加载会话
session = create_or_load_session(
    "STM32F411RE Nucleo 板，PA5 LED 每 500ms 闪烁"
)

print(f"Session ID: {session.session_id}")
print(f"项目: {session.project_context.project_name}")
```

### 记录交互

```python
from stloop.memory import get_memory_manager

manager = get_memory_manager()

# 记录用户请求
user_input = "添加串口输出，波特率 115200"
agent_response = "好的，我将添加 USART2 串口输出"

turn = manager.record_interaction(
    user_input=user_input,
    agent_response=agent_response,
    action_taken="add_uart"
)

# 执行操作后更新上下文
manager.update_turn_context_after_action(
    turn=turn,
    new_context_changes={
        "peripherals": ["GPIO", "TIM", "USART2"],
        "features": ["LED blink", "500ms interval", "UART output 115200"],
    },
    code_changes=["src/main.c", "src/uart.c"],
)
```

### 获取智能建议

```python
from stloop.memory import get_memory_manager

manager = get_memory_manager()

# 获取建议
suggestions = manager.suggest_next_steps()
for i, suggestion in enumerate(suggestions, 1):
    print(f"{i}. {suggestion}")

# 输出:
# 1. 编译并仿真测试
# 2. 添加串口输出调试信息
# 3. 查看项目状态
```

### 导出项目文档

```python
from stloop.memory import get_memory_manager

manager = get_memory_manager()

# 导出 Markdown 格式摘要
md_content = manager.export_project_summary()

# 保存到文件
with open("PROJECT_SUMMARY.md", "w", encoding="utf-8") as f:
    f.write(md_content)
```

## 存储位置

项目记忆数据存储在：

```
Windows: C:\Users\<用户名>\.stloop\memory\session_xxx.json
Linux/Mac: ~/.stloop/memory/session_xxx.json
```

## 数据结构

### Session（会话）

```json
{
  "session_id": "session_20240318_143022_abc123",
  "project_context": {
    "project_name": "STM32F411RE_LED_blink",
    "description": "STM32F411RE 开发板，PA5 LED 闪烁",
    "mcu_model": "STM32F411RE",
    "framework": "cube",
    "features": ["LED blink", "500ms interval"],
    "peripherals": ["GPIO", "TIM"],
    "current_status": "developing",
    "last_modified": "2024-03-18T14:30:22.123456"
  },
  "conversation_history": [...],
  "task_queue": [...],
  "completed_tasks": [...]
}
```

### ConversationTurn（对话回合）

```json
{
  "turn_id": 1,
  "user_input": "生成 LED 闪烁代码",
  "agent_response": "已生成代码，使用 PA5 GPIO",
  "action_taken": "code_generation",
  "project_context_before": {...},
  "project_context_after": {...},
  "timestamp": "2024-03-18T14:30:22.123456"
}
```

## 与 CLI 集成

### 命令行参数

```bash
# 继续最近会话
stloop --continue
stloop -c

# 指定会话
stloop --session session_xxx
stloop -s session_xxx

# 列出所有会话
stloop --list-sessions

# 交互式选择会话
stloop --select-session
```

### 交互式命令

在 STLoop 交互模式下：

```
> status              # 查看项目状态
> tasks               # 查看任务列表
> add_task <描述>     # 添加任务
> complete_task <id>  # 完成任务
> export              # 导出项目摘要
> sessions            # 列出所有会话
> switch <session_id> # 切换会话
```

## 示例工作流

### 场景 1：初次使用

```bash
$ python -m stloop

STLoop > STM32F411RE 开发板，PA5 LED 每 500ms 闪烁一次，同时 USART2 输出调试信息

[系统] 创建新会话: STM32F411RE_开发板_PA5_LED
[系统] Session ID: session_20240318_143022_abc123

[思考] 推断 MCU: STM32F411RE
[思考] 功能: LED 闪烁 + 串口输出
[思考] 外设: GPIO, TIM, USART2

[操作] 生成代码...
[完成] 代码已生成: generated/
[建议] 下一步：
  1. 编译并仿真测试
  2. 查看生成的代码

> 编译
[操作] 编译项目...
[完成] 编译成功: build/stm32_app.elf (16 KB)
[建议] 下一步：
  1. 启动仿真
  2. 烧录到硬件

> 仿真
[操作] 启动 Renode 仿真...
[提示] 按 Ctrl+C 停止仿真
[仿真输出] LED 状态: ON
[仿真输出] LED 状态: OFF
...

> status
项目: STM32F411RE_开发板_PA5_LED
状态: developing
功能: LED blink, 500ms interval, UART output 115200
外设: GPIO, TIM, USART2
```

### 场景 2：次日继续

```bash
$ python -m stloop --continue

[系统] 加载会话: STM32F411RE_开发板_PA5_LED
[系统] 上次更新: 2024-03-18 14:30

[摘要] 当前项目状态:
  - 已实现: LED 闪烁 + 串口输出
  - 待办: 添加 ADC 采集功能
  - 上次: 完成编译和仿真

> 添加 ADC 采集，PA0 引脚
[思考] 已有功能: LED blink, UART output
[思考] 新增功能: ADC 采集
[思考] 新增外设: ADC1, PA0

[操作] 修改代码...
[完成] 已添加 ADC 采集功能

> complete_task task_2 ADC 功能添加完成，采样率 1kHz
[系统] 任务已完成，上下文已更新
```

## 高级功能

### 1. 相似项目检测

```python
from stloop.memory import find_similar_projects

# 查找相似项目
similar = find_similar_projects(
    "STM32F411RE LED 闪烁",
    threshold=0.6  # 相似度阈值
)

for session in similar:
    print(f"{session.project_context.project_name}")
    print(f"  相似度: {similarity}")
```

### 2. 批量导出

```python
from stloop.memory import ProjectMemoryManager

manager = ProjectMemoryManager()

# 导出所有会话摘要
for session in manager.list_sessions():
    md = manager.export_project_summary()
    filename = f"{session.session_id}.md"
    with open(filename, "w") as f:
        f.write(md)
```

### 3. 自定义上下文字段

```python
from stloop.memory import ProjectContext

# 扩展上下文
context = ProjectContext(
    project_name="MyProject",
    description="...",
    custom_field="custom_value"  # 自定义字段
)
```

## 故障排除

### 会话丢失

如果会话意外丢失，检查：

```bash
# 查看存储目录
ls ~/.stloop/memory/

# 手动加载
python -c "
from stloop.memory import ProjectMemoryManager
m = ProjectMemoryManager()
sessions = m.list_sessions()
for s in sessions:
    print(f'{s.session_id}: {s.project_context.project_name}')
"
```

### 上下文未更新

确保调用了 `update_turn_context_after_action`：

```python
# 错误：只调用了 record_interaction
turn = manager.record_interaction(...)
# 忘记调用 update_turn_context_after_action！

# 正确：
turn = manager.record_interaction(...)
manager.update_turn_context_after_action(turn, {...}, [...])
```

## 未来扩展

计划添加的功能：

1. **语义搜索** - 使用 embeddings 搜索相似项目
2. **代码变更追踪** - 记录每次修改的 diff
3. **协作支持** - 多用户共享项目记忆
4. **云端同步** - 跨设备同步会话
5. **可视化仪表板** - Web 界面查看项目进度
