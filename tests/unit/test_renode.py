#!/usr/bin/env python3
"""测试 Renode 集成"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from stloop.ui import get_console
from stloop.ui.components import render_header
from stloop.simulators import (
    RenodeSimulator,
    find_renode_bin,
    get_platform_file,
    list_supported_platforms,
)


def test_renode_installation():
    """测试 Renode 安装"""
    console = get_console()
    console.print("\n[cyan]Testing Renode installation...[/cyan]")

    bin_path = find_renode_bin()
    if bin_path:
        console.print(f"[green][OK] Renode found: {bin_path}[/green]")
        return True
    else:
        console.print("[yellow][!] Renode not found in PATH[/yellow]")
        console.print("[dim]Install from: https://renode.io/#downloads[/dim]")
        return False


def test_platform_mapping():
    """测试平台映射"""
    console = get_console()
    console.print("\n[cyan]Testing platform mapping...[/cyan]")

    # 测试已知 MCU
    platform = get_platform_file("STM32F411RE")
    if platform:
        console.print(f"[green][OK] STM32F411RE -> {platform}[/green]")
    else:
        console.print("[red][X] STM32F411RE not found[/red]")
        return False

    # 测试列表
    platforms = list_supported_platforms()
    console.print(f"[green][OK] {len(platforms)} platforms supported[/green]")

    return True


def test_simulator_class():
    """测试仿真器类"""
    console = get_console()
    console.print("\n[cyan]Testing RenodeSimulator class...[/cyan]")

    try:
        sim = RenodeSimulator()

        if sim.is_installed():
            console.print("[green][OK] Simulator initialized (Renode installed)[/green]")
        else:
            console.print("[yellow][!] Simulator initialized (Renode not installed)[/yellow]")

        return True
    except Exception as e:
        console.print(f"[red][X] Error: {e}[/red]")
        return False


def test_script_generation():
    """测试脚本生成"""
    console = get_console()
    console.print("\n[cyan]Testing .resc script generation...[/cyan]")

    try:
        from stloop.simulators import generate_resc_script

        # 创建临时 ELF 路径
        test_elf = Path("/tmp/test.elf")

        script_path = generate_resc_script(
            test_elf,
            mcu="STM32F411RE",
            output_path=Path("/tmp/test_simulation.resc"),
        )

        if script_path.exists():
            console.print(f"[green][OK] Script generated: {script_path}[/green]")

            # 显示内容预览
            content = script_path.read_text()
            console.print("[dim]Preview:[/dim]")
            for line in content.split("\n")[:10]:
                console.print(f"  {line}")

            # 清理
            script_path.unlink()
            return True
        else:
            console.print("[red][X] Script not created[/red]")
            return False

    except Exception as e:
        console.print(f"[red][X] Error: {e}[/red]")
        return False


def main():
    console = get_console()

    render_header("Renode Integration Test")

    tests = [
        ("Installation", test_renode_installation),
        ("Platform Mapping", test_platform_mapping),
        ("Simulator Class", test_simulator_class),
        ("Script Generation", test_script_generation),
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

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
