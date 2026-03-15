#!/usr/bin/env python3
"""Serial Monitor 测试脚本"""

import sys
import time
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from stloop.ui import get_console, SerialMonitor, DisplayMode, LogLevel
from stloop.ui.components import render_header


def test_log_detection():
    """测试日志级别识别"""
    console = get_console()

    print("\n=== Test: Log Level Detection ===")

    monitor = SerialMonitor(console)

    test_cases = [
        (b"[INFO] System started", LogLevel.INFO),
        (b"[DEBUG] Variable x=42", LogLevel.DEBUG),
        (b"[ERROR] Failed to open file", LogLevel.ERROR),
        (b"[WARNING] Low memory", LogLevel.WARNING),
        (b"[CRITICAL] System crash!", LogLevel.CRITICAL),
        (b"Regular message", LogLevel.UNKNOWN),
    ]

    for data, expected in test_cases:
        detected = monitor.detect_level(data)
        status = "[OK]" if detected == expected else "[X]"
        console.print(f"{status} {data!r:40} -> {detected.value}")


def test_message_formatting():
    """测试消息格式化"""
    console = get_console()

    print("\n=== Test: Message Formatting ===")

    from stloop.ui.serial_monitor import SerialMessage

    monitor = SerialMonitor(console)

    # 创建测试消息
    msg = SerialMessage(
        timestamp=datetime.now(),
        data=b"[INFO] LED State: ON",
        level=LogLevel.INFO,
    )

    # 测试不同显示模式
    console.print("\n[cyan]Text Mode:[/cyan]")
    monitor.display_mode = DisplayMode.TEXT
    console.print(monitor.format_message(msg))

    console.print("\n[cyan]Hex Mode:[/cyan]")
    monitor.display_mode = DisplayMode.HEX
    console.print(monitor.format_message(msg))

    console.print("\n[cyan]Mixed Mode:[/cyan]")
    monitor.display_mode = DisplayMode.MIXED
    console.print(monitor.format_message(msg))


def test_history_rendering():
    """测试历史记录渲染"""
    console = get_console()

    print("\n=== Test: History Rendering ===")

    from stloop.ui.serial_monitor import SerialMessage

    monitor = SerialMonitor(console, max_history=100)

    # 模拟一些历史消息
    messages = [
        (b"[INFO] System initialized", LogLevel.INFO),
        (b"[DEBUG] GPIO configured", LogLevel.DEBUG),
        (b"[INFO] LED State: ON", LogLevel.INFO),
        (b"[WARN] Temperature high", LogLevel.WARNING),
        (b"[INFO] LED State: OFF", LogLevel.INFO),
        (b"[ERROR] Communication timeout", LogLevel.ERROR),
    ]

    for data, level in messages:
        msg = SerialMessage(
            timestamp=datetime.now(),
            data=data,
            level=level,
        )
        monitor.history.append(msg)

    # 渲染面板
    console.print(monitor.render(max_lines=10))


def test_port_listing():
    """测试串口列表"""
    console = get_console()

    print("\n=== Test: Port Listing ===")

    ports = SerialMonitor.list_ports()

    if ports:
        console.print(f"[green][OK] Found {len(ports)} port(s):[/green]")
        for port in ports:
            console.print(f"  - {port['device']}: {port['description']}")
    else:
        console.print(
            "[yellow][!] No serial ports found (this is normal if no devices connected)[/yellow]"
        )


def test_status_display():
    """测试状态显示"""
    console = get_console()

    print("\n=== Test: Status Display ===")

    monitor = SerialMonitor(console)

    # 未连接状态
    console.print(f"Disconnected: {monitor.render_status()}")

    # 模拟连接状态
    monitor.connected = True
    monitor.port_name = "COM3"
    monitor.baudrate = 115200
    monitor.bytes_received = 1024
    monitor.lines_received = 42
    monitor.start_time = datetime.now()

    console.print(f"Connected: {monitor.render_status()}")


def test_mock_connection():
    """测试模拟连接和数据显示"""
    console = get_console()

    print("\n=== Test: Mock Connection ===")

    monitor = SerialMonitor(console, max_history=50)

    # 模拟连接（不实际打开串口）
    monitor.connected = True
    monitor.port_name = "MOCK"
    monitor.baudrate = 115200
    monitor.start_time = datetime.now()

    # 模拟接收数据
    from stloop.ui.serial_monitor import SerialMessage

    mock_messages = [
        b"[INFO] Bootloader started",
        b"[INFO] Firmware version: 1.0.0",
        b"[DEBUG] Clock: 100MHz",
        b"[INFO] GPIO initialized",
        b"[INFO] Main loop started",
        b"[WARN] Watchdog enabled",
    ]

    console.print("[cyan]Simulating data reception...[/cyan]\n")

    for data in mock_messages:
        msg = SerialMessage(
            timestamp=datetime.now(),
            data=data,
            level=monitor.detect_level(data),
        )
        monitor.history.append(msg)
        monitor.bytes_received += len(data)
        monitor.lines_received += 1

        console.print(monitor.format_message(msg))
        time.sleep(0.1)

    console.print("\n")
    console.print(monitor.render(max_lines=15))


def main():
    console = get_console()

    print("[bold cyan]STLoop Serial Monitor Test[/bold cyan]\n")

    tests = [
        ("Log Level Detection", test_log_detection),
        ("Message Formatting", test_message_formatting),
        ("History Rendering", test_history_rendering),
        ("Port Listing", test_port_listing),
        ("Status Display", test_status_display),
        ("Mock Connection", test_mock_connection),
    ]

    for name, test_func in tests:
        try:
            test_func()
            console.print(f"\n[green][OK] {name} passed[/green]")
        except Exception as e:
            console.print(f"\n[red][X] {name} failed: {e}[/red]")
            import traceback

            traceback.print_exc()

    console.print("\n[bold green]All tests completed![/bold green]")


if __name__ == "__main__":
    main()
