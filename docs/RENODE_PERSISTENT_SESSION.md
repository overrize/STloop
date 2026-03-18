# Renode 持久化仿真会话

## 当前结束逻辑的问题

当你运行 `stloop gen "xxx" --sim` 时：

1. **Renode 启动** → 加载 ELF → 开始仿真
2. **用户按 Ctrl+C** → Renode 进程被终止
3. **仿真状态丢失** → UART 输出消失 → 无法重新连接

**问题**：一旦终端关闭，你无法：
- 重新查看 UART 输出
- 重新连接 GDB
- 暂停/继续仿真

## 新方案：持久化会话

### 核心设计

```
启动仿真 → 创建 Session → 后台运行 Renode
    ↓              ↓              ↓
生成脚本    保存到 ~/.stloop/    Monitor Socket
    ↓              ↓              ↓
可重新打开   记录端口/状态     支持 telnet 连接
```

### 功能

1. **后台持久运行**
   - Renode 在后台运行（不是当前终端的子进程）
   - 关闭终端不会停止仿真
   - 支持重新连接

2. **多方式连接**
   ```
   ┌─────────────────────────────────────┐
   │         Renode (后台运行)            │
   │  ┌─────────┐  ┌─────────┐          │
   │  │ Monitor │  │  GDB    │          │
   │  │ :1234   │  │ :3333   │          │
   │  └────┬────┘  └────┬────┘          │
   │       │            │               │
   │  ┌────▼────────────▼────┐          │
   │  │    UART Logger       │          │
   │  │  (保存到文件)         │          │
   │  └──────────────────────┘          │
   └─────────────────────────────────────┘
   ```

3. **重新打开方式**
   - **方式1**: 双击 `重新打开终端查看仿真.bat`
   - **方式2**: 命令行 `stloop sim --reopen`
   - **方式3**: telnet `telnet localhost 1234`
   - **方式4**: GDB `arm-none-eabi-gdb -ex 'target remote localhost:3333'`

## 使用示例

### 启动持久化仿真

```python
from stloop.simulators.renode_session import RenodeSessionManager

manager = RenodeSessionManager()

# 启动仿真（后台运行）
session = manager.start_persistent_simulation(
    elf_path="build/stm32_app.elf",
    mcu="STM32F411RE"
)

print(f"Session ID: {session.session_id}")
print(f"Telnet: telnet localhost {session.telnet_port}")
print(f"GDB: localhost:{session.gdb_port}")
```

### 重新打开会话

```bash
# 方法1: 使用 stloop 命令
stloop sim --reopen                    # 打开最新会话
stloop sim --reopen session_20240318   # 打开指定会话

# 方法2: 双击脚本
cd build
双击 "_重新打开仿真终端.bat"

# 方法3: 手动连接
telnet localhost 1234                  # 进入 monitor
# 输入: pause, continue, quit, help
```

### 查看 UART 输出

```bash
# Windows (PowerShell)
Get-Content .stloop/renode_sessions/session_xxx/uart.log -Wait

# Linux/Mac
tail -f ~/.stloop/renode_sessions/session_xxx/uart.log
```

## 实现细节

### 生成的文件结构

```
~/.stloop/renode_sessions/session_20240318_143022/
├── session.json              # 会话配置
├── persistent_simulation.resc # Renode 脚本
├── renode.log               # Renode 输出日志
├── uart.log                 # UART 输出
├── pid.txt                  # 进程 ID
├── reopen.ps1              # Windows 重开脚本
├── reopen.sh               # Linux/Mac 重开脚本
└── 重新打开终端查看仿真.bat   # Windows 快捷方式

# 同时在项目目录也放一个快捷方式
build/
└── _重新打开仿真终端.bat      # 指向上述脚本
```

### Resc 脚本差异

**旧脚本**（一次性）：
```renode
mach create "STM32F411RE"
machine LoadPlatformDescription @stm32f4.repl
sysbus LoadELF "firmware.elf"
start  ; ← 直接启动，无 socket
```

**新脚本**（持久化）：
```renode
mach create "STM32F411RE"
machine LoadPlatformDescription @stm32f4.repl

; 创建 monitor socket（关键）
emulation CreateServerSocketTerminal 1234 "monitor" false
machine SetPrimaryConsole monitor

sysbus LoadELF "firmware.elf"
emulation CreateFileBackedUartTerminal "uart.log"
connector Connect sysbus.usart1 terminal

machine StartGdbServer 3333
start
```

## 待办：集成到 stloop CLI

### 1. 添加 `--persistent` 标志

```python
# cli_rich.py
def _cmd_gen(...):
    if args.sim:
        if args.persistent:
            # 使用新的持久化方式
            from stloop.simulators.renode_session import RenodeSessionManager
            manager = RenodeSessionManager()
            session = manager.start_persistent_simulation(elf, args.mcu)
            console.print(f"[OK] 持久化仿真已启动: {session.session_id}")
            console.print(f"重新打开: stloop sim --reopen {session.session_id}")
        else:
            # 原有的一次性仿真
            sim = RenodeSimulator()
            sim.start(elf, args.mcu, blocking=True)
```

### 2. 添加 `sim` 子命令

```python
# cli_rich.py 添加
sub Sim:
    - stloop sim --list              # 列出所有会话
    - stloop sim --reopen [id]       # 重新打开会话
    - stloop sim --connect [id]      # telnet 连接
    - stloop sim --stop [id]         # 停止会话
```

## 优势对比

| 特性 | 旧方式 | 新方式 |
|------|--------|--------|
| 终端关闭后仿真继续 | ❌ | ✅ |
| 重新查看 UART | ❌ | ✅ |
| GDB 重新连接 | ❌ | ✅ |
| 多终端同时连接 | ❌ | ✅ |
| 暂停/继续控制 | ❌ | ✅ |
| 仿真状态保存 | ❌ | ✅ |

## 下一步

1. **集成到 CLI**: 添加 `--persistent` 和 `sim` 子命令
2. **GUI 支持**: 在 reopen 窗口中添加按钮控制（暂停、继续、复位）
3. **状态保存**: 支持保存完整仿真状态，之后恢复
4. **多会话**: 同时运行多个仿真，分别管理
