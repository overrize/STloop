#!/usr/bin/env python3
"""测试 Phase 5: Serial Monitor 集成"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from stloop.ui import get_console, SerialMonitor


def test_monitor_import():
    """测试导入"""
    console = get_console()
    console.print("[cyan]Testing Serial Monitor import...[/cyan]")

    try:
        from stloop.chat_rich import _start_serial_monitor_ui

        console.print("[green][OK] _start_serial_monitor_ui imported[/green]")
        return True
    except ImportError as e:
        console.print(f"[red][X] Import failed[/red]")
        return False


def test_cli_commands():
    """测试 CLI 命令"""
    console = get_console()
    console.print("\n[cyan]Testing CLI commands...[/cyan]")

    import subprocess

    # 检查主命令 help
    result = subprocess.run(
        [sys.executable, "-m", "stloop", "--help"], capture_output=True, text=True
    )

    has_monitor = "monitor" in result.stdout

    if has_monitor:
        console.print("OK: monitor command available")
    else:
        console.print("FAIL: monitor command not found")
        return False

    # 检查 gen 子命令 help
    result = subprocess.run(
        [sys.executable, "-m", "stloop", "gen", "--help"], capture_output=True, text=True
    )

    has_option = "--monitor" in result.stdout

    if has_option:
        console.print("OK: --monitor option in gen command")
    else:
        console.print("FAIL: --monitor option not in gen command")
        return False

    return True


def test_port_listing():
    """测试串口列表"""
    console = get_console()
    console.print("\n[cyan]Testing port listing...[/cyan]")

    try:
        ports = SerialMonitor.list_ports()
        console.print(f"OK: Found {len(ports)} port(s)")

        for port in ports:
            console.print(f"  - {port['device']}: {port['description']}")

        return True
    except Exception as e:
        console.print(f"FAIL: {e}")
        return False


def test_monitor_creation():
    """测试监控器创建"""
    console = get_console()
    console.print("\n[cyan]Testing monitor creation...[/cyan]")

    try:
        monitor = SerialMonitor(console)
        console.print("OK: SerialMonitor created")

        # 测试未连接状态
        status = monitor.render_status()
        console.print(f"  Status: {status}")

        return True
    except Exception as e:
        console.print(f"FAIL: {e}")
        return False


def main():
    console = get_console()

    console.print("[bold cyan]Phase 5: Serial Monitor Integration Test[/bold cyan]\n")

    tests = [
        ("Monitor Import", test_monitor_import),
        ("CLI Commands", test_cli_commands),
        ("Port Listing", test_port_listing),
        ("Monitor Creation", test_monitor_creation),
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        try:
            if test_func():
                console.print(f"\n[green]PASSED: {name}[/green]")
                passed += 1
            else:
                console.print(f"\n[red]FAILED: {name}[/red]")
                failed += 1
        except Exception as e:
            console.print(f"\n[red]ERROR: {name} - {e}[/red]")
            import traceback

            traceback.print_exc()
            failed += 1

    console.print(f"\n[bold]Results: {passed} passed, {failed} failed[/bold]")

    if failed == 0:
        console.print("[bold green]Phase 5 complete![/bold green]")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
