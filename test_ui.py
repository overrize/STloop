#!/usr/bin/env python3
"""
UI 组件测试脚本

运行此脚本验证 Phase 1 的 UI 组件是否正常工作。
"""

import time
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from stloop.ui import get_console
from stloop.ui.components import (
    render_splash,
    render_header,
    render_section_header,
    create_info_panel,
    create_success_panel,
    create_error_panel,
    create_code_panel,
    create_progress,
    StepIndicator,
    create_spinner,
)


def test_splash():
    """测试启动画面"""
    print("\n" + "=" * 60)
    print("Test 1: Splash Screen")
    print("=" * 60)
    render_splash()
    time.sleep(1)


def test_panels():
    """测试面板组件"""
    console = get_console()

    print("\n" + "=" * 60)
    print("Test 2: Panel Components")
    print("=" * 60)

    # Info Panel
    console.print(
        create_info_panel(
            "This is an information panel\nWith multiple lines of content.", title="ℹ️ Info"
        )
    )

    # Success Panel
    console.print(
        create_success_panel(
            "Build completed successfully!",
            title="✓ Success",
            details={"Target": "STM32F411RE", "Size": "12.4 KB", "Time": "3.2s"},
        )
    )

    # Error Panel
    console.print(
        create_error_panel(
            "Failed to compile main.c",
            title="❌ Error",
            suggestions=[
                "Check syntax errors in line 45",
                "Verify header file includes",
                "Run 'stloop check' to verify toolchain",
            ],
        )
    )


def test_code_panel():
    """测试代码面板"""
    console = get_console()

    print("\n" + "=" * 60)
    print("Test 3: Code Panel")
    print("=" * 60)

    code = """#include "stm32f4xx_hal.h"

void SystemClock_Config(void) {
    // Enable HSE
    RCC_OscInitTypeDef RCC_OscInitStruct = {0};
    RCC_OscInitStruct.OscillatorType = RCC_OSCILLATORTYPE_HSE;
    RCC_OscInitStruct.HSEState = RCC_HSE_ON;
    HAL_RCC_OscConfig(&RCC_OscInitStruct);
}

int main(void) {
    HAL_Init();
    SystemClock_Config();
    
    while (1) {
        HAL_GPIO_TogglePin(GPIOA, GPIO_PIN_5);
        HAL_Delay(500);
    }
}"""

    console.print(create_code_panel(code, title="main.c"))


def test_progress():
    """测试进度条"""
    console = get_console()

    print("\n" + "=" * 60)
    print("Test 4: Progress Bar")
    print("=" * 60)

    with create_progress() as progress:
        task = progress.add_task("Downloading...", total=100)

        for i in range(100):
            progress.update(task, advance=1)
            time.sleep(0.02)


def test_step_indicator():
    """测试步骤指示器"""
    console = get_console()

    print("\n" + "=" * 60)
    print("Test 5: Step Indicator")
    print("=" * 60)

    steps = [
        "Parse Requirements",
        "Load Hardware Context",
        "Query AI Agent",
        "Generate Code",
        "Validate Syntax",
    ]

    indicator = StepIndicator(steps)
    indicator.render()

    for step in steps:
        time.sleep(0.5)
        indicator.next()


def test_spinner():
    """测试 Spinner"""
    print("\n" + "=" * 60)
    print("Test 6: Spinner")
    print("=" * 60)

    with create_spinner("Connecting to target..."):
        time.sleep(2)

    print("✓ Connected!")


def test_full_ui():
    """测试完整 UI 流程"""
    console = get_console()

    print("\n" + "=" * 60)
    print("Test 7: Full UI Flow")
    print("=" * 60)

    # 清屏并显示启动画面
    console.clear()
    render_splash()
    time.sleep(1)

    # 显示头部
    render_header("Code Generation", subtitle="STM32F411RE")

    # 显示步骤
    steps = ["Analyze", "Generate", "Compile", "Flash"]
    indicator = StepIndicator(steps)
    indicator.render()

    # 模拟流程
    time.sleep(0.5)
    indicator.next()

    with create_spinner("Querying AI Agent..."):
        time.sleep(1.5)

    indicator.next()
    console.print(create_success_panel("Code generated successfully!"))

    time.sleep(0.5)
    indicator.next()

    with create_progress() as progress:
        task = progress.add_task("Compiling...", total=100)
        for i in range(100):
            progress.update(task, advance=1)
            time.sleep(0.01)

    console.print(
        create_success_panel(
            "Build completed!", details={"ELF": "12.4 KB", "BIN": "8.2 KB", "Time": "2.1s"}
        )
    )


def main():
    """运行所有测试"""
    console = get_console()

    print("[bold cyan]STLoop UI Components Test[/bold cyan]")
    print("Testing Phase 1: Basic UI Framework\n")

    tests = [
        ("Splash Screen", test_splash),
        ("Panels", test_panels),
        ("Code Panel", test_code_panel),
        ("Progress Bar", test_progress),
        ("Step Indicator", test_step_indicator),
        ("Spinner", test_spinner),
        ("Full UI Flow", test_full_ui),
    ]

    for name, test_func in tests:
        try:
            test_func()
            console.print(f"[green]✓ {name} passed[/green]")
        except Exception as e:
            console.print(f"[red]✗ {name} failed: {e}[/red]")

    print("\n[bold green]All tests completed![/bold green]")


if __name__ == "__main__":
    main()
