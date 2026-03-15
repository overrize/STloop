#!/usr/bin/env python3
"""Hardware Catalog 测试脚本"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from stloop.ui import get_console, HardwareCatalog, select_mcu
from stloop.ui.components import render_header
from stloop.hardware.mcu_database import MCUFamily


def test_catalog_render():
    """测试目录渲染"""
    console = get_console()

    print("\n=== Test: Catalog Render ===")
    render_header("Hardware Catalog Test")

    catalog = HardwareCatalog(console)
    console.print(catalog.render())


def test_catalog_search():
    """测试搜索功能"""
    console = get_console()

    print("\n=== Test: Catalog Search ===")

    catalog = HardwareCatalog(console)

    # 搜索 STM32
    catalog.filter("STM32F4")
    console.print("\n[cyan]Search: STM32F4[/cyan]")
    console.print(catalog.render())

    # 搜索 ESP32
    catalog.filter("ESP32")
    console.print("\n[cyan]Search: ESP32[/cyan]")
    console.print(catalog.render())

    # 清空搜索
    catalog.filter("")


def test_catalog_details():
    """测试详情展示"""
    console = get_console()

    print("\n=== Test: Catalog Details ===")

    catalog = HardwareCatalog(console)

    # 显示第一个 MCU 的详情
    if catalog.filtered_mcus:
        mcu = catalog.filtered_mcus[0]
        console.print(catalog.render_details(mcu))


def test_select_mcu():
    """测试交互式选择"""
    console = get_console()

    print("\n=== Test: Select MCU (Interactive) ===")

    # 显示目录（非交互式）
    catalog = HardwareCatalog(console)
    console.print(catalog.render())
    console.print("\n[dim]In real app, this would be interactive[/dim]")


def test_family_filter():
    """测试系列过滤"""
    console = get_console()

    print("\n=== Test: Family Filter ===")

    catalog = HardwareCatalog(console)

    # 只显示 ESP32
    catalog.mcus = [mcu for mcu in catalog.mcus if mcu.family == MCUFamily.ESP32]
    catalog.filtered_mcus = catalog.mcus

    console.print("\n[cyan]ESP32 Series Only:[/cyan]")
    console.print(catalog.render())


def main():
    console = get_console()

    print("[bold cyan]STLoop Hardware Catalog Test[/bold cyan]\n")

    tests = [
        ("Catalog Render", test_catalog_render),
        ("Catalog Search", test_catalog_search),
        ("Catalog Details", test_catalog_details),
        ("Family Filter", test_family_filter),
        ("Select MCU", test_select_mcu),
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
