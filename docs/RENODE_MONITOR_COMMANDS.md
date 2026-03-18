# Renode Monitor 命令指南

## 问题诊断

**错误示例：**
```renode
(monitor) sysbus.usart1
No such command or device: sysbus.usart1

(monitor) showDevices
No such command or device: showDevices
```

**原因：**
在 `(monitor)` 提示符下（没有创建 machine 之前），`sysbus` 和其他设备相关命令不可用。

## 正确的工作流程

### 1. 创建机器
```renode
(monitor) mach create "my_stm32"
(machine-0)
```

### 2. 加载平台
```renode
(machine-0) machine LoadPlatformDescription @platforms/cpus/stm32f4.repl
```

### 3. 加载固件
```renode
(machine-0) sysbus LoadELF "firmware.elf"
```

### 4. 启动仿真
```renode
(machine-0) start
```

## 常用命令速查

| 命令 | 说明 | 可用层级 |
|------|------|----------|
| `mach create "name"` | 创建机器 | (monitor) |
| `mach list` | 列出所有机器 | (monitor) |
| `using sysbus` | 设置默认前缀 | (machine) |
| `machine LoadPlatformDescription @path` | 加载平台 | (machine) |
| `sysbus LoadELF "file"` | 加载固件 | (machine) |
| `sysbus ReadDoubleWord 0x08000000` | 读取内存 | (machine) |
| `start` | 启动仿真 | (machine) |
| `pause` | 暂停仿真 | (machine) |
| `continue` | 继续仿真 | (machine) |
| `reset` | 复位机器 | (machine) |
| `quit` | 退出 Renode | (any) |
| `help` | 查看帮助 | (any) |
| `help <command>` | 查看具体命令帮助 | (any) |

## 快速脚本示例

创建 `start.resc` 文件：
```renode
; 创建机器
mach create "stm32f411re"

; 加载平台
machine LoadPlatformDescription @platforms/cpus/stm32f4.repl

; 加载固件
sysbus LoadELF "build/stm32_app.elf"

; 启动 GDB 服务器（可选）
machine StartGdbServer 3333

; 开始仿真
start
```

运行：
```bash
renode start.resc
```

## 与 STLoop 集成

当使用 `stloop gen "..." --sim` 时，STLoop 会自动生成 `.resc` 脚本并启动 Renode。

如果需要手动加载脚本：
```renode
(monitor) include @path/to/simulation.resc
```

**注意：** 是 `include` 不是 `i`！
