#!/usr/bin/env python3
"""测试重构后的主流程"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from stloop.ui import get_console
from stloop.ui.components import render_splash, render_header
from stloop.hardware.mcu_database import get_mcu


def test_imports():
    """测试所有导入"""
    console = get_console()
    console.print("[cyan]Testing imports...[/cyan]")

    try:
        from stloop.cli_rich import main, _cmd_chat, _cmd_catalog, _cmd_check
        from stloop.chat_rich import run_interactive_rich

        console.print("[green][OK] All imports successful[/green]")
        return True
    except Exception as e:
        console.print(f"[red][X] Import failed: {e}[/red]")
        return False


def test_splash():
    """测试启动画面"""
    console = get_console()
    console.print("\n[cyan]Testing splash screen...[/cyan]")

    try:
        render_splash()
        return True
    except Exception as e:
        console.print(f"[red][X] Splash failed: {e}[/red]")
        return False


def test_hardware_catalog():
    """测试硬件目录"""
    console = get_console()
    console.print("\n[cyan]Testing hardware catalog...[/cyan]")

    try:
        from stloop.ui import HardwareCatalog

        catalog = HardwareCatalog(console)
        console.print(catalog.render())

        # 测试搜索
        catalog.filter("STM32F4")
        console.print(f"\n[cyan]Search 'STM32F4': {len(catalog.filtered_mcus)} results[/cyan]")

        return True
    except Exception as e:
        console.print(f"[red][X] Catalog failed: {e}[/red]")
        return False


def test_mcu_database():
    """测试 MCU 数据库"""
    console = get_console()
    console.print("\n[cyan]Testing MCU database...[/cyan]")

    try:
        mcu = get_mcu("STM32F411RE")
        if mcu:
            console.print(f"[green][OK] Found: {mcu.name}[/green]")
            console.print(f"  Core: {mcu.core.value}")
            console.print(f"  Flash: {mcu.flash_kb}KB, RAM: {mcu.ram_kb}KB")
            return True
        else:
            console.print("[red][X] MCU not found[/red]")
            return False
    except Exception as e:
        console.print(f"[red][X] Database failed: {e}[/red]")
        return False


def test_ui_components():
    """测试 UI 组件"""
    console = get_console()
    console.print("\n[cyan]Testing UI components...[/cyan]")

    try:
        from stloop.ui.components import (
            create_success_panel,
            create_error_panel,
            create_info_panel,
            StepIndicator,
        )

        console.print(create_info_panel("Test info message", title="Info"))
        console.print(create_success_panel("Test success", details={"Key": "Value"}))

        steps = ["Step 1", "Step 2", "Step 3"]
        indicator = StepIndicator(steps)
        indicator.render()

        return True
    except Exception as e:
        console.print(f"[red][X] UI components failed: {e}[/red]")
        return False


def main():
    console = get_console()

    console.print("[bold cyan]STLoop Refactored Flow Test[/bold cyan]\n")

    tests = [
        ("Imports", test_imports),
        ("Splash Screen", test_splash),
        ("MCU Database", test_mcu_database),
        ("Hardware Catalog", test_hardware_catalog),
        ("UI Components", test_ui_components),
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        try:
            if test_func():
                console.print(f"\n[green][OK] {name} passed[/green]")
                passed += 1
            else:
                console.print(f"\n[red][X] {name} failed[/red]")
                failed += 1
        except Exception as e:
            console.print(f"\n[red][X] {name} error: {e}[/red]")
            failed += 1

    console.print(f"\n[bold]{'=' * 50}[/bold]")
    console.print(f"[bold]Results: {passed} passed, {failed} failed[/bold]")

    if failed == 0:
        console.print("[bold green]All tests passed! Ready to use.[/bold green]")
    else:
        console.print("[bold yellow]Some tests failed. Check errors above.[/bold yellow]")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
