#!/usr/bin/env python3
"""UI 组件测试脚本"""

import time
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from stloop.ui import get_console
from stloop.ui.components import (
    render_splash,
    render_header,
    create_info_panel,
    create_success_panel,
    create_error_panel,
    create_code_panel,
    create_progress,
    StepIndicator,
    create_spinner,
)


def test_panels():
    console = get_console()
    print("\n=== Test: Panels ===")

    console.print(create_info_panel("Information panel content", title="Info"))
    console.print(create_success_panel("Success!", title="Done", details={"Key": "Value"}))
    console.print(create_error_panel("Error!", title="Failed", suggestions=["Fix 1", "Fix 2"]))


def test_progress():
    print("\n=== Test: Progress ===")
    with create_progress() as progress:
        task = progress.add_task("Working...", total=50)
        for i in range(50):
            progress.update(task, advance=1)
            time.sleep(0.01)


def test_steps():
    print("\n=== Test: Steps ===")
    steps = ["Step 1", "Step 2", "Step 3"]
    indicator = StepIndicator(steps)
    indicator.render()
    for _ in steps:
        time.sleep(0.3)
        indicator.next()


def main():
    console = get_console()
    print("[bold cyan]STLoop UI Test[/bold cyan]")

    render_splash()
    time.sleep(0.5)

    test_panels()
    test_progress()
    test_steps()

    console.print("\n[green][OK] All tests passed![/green]")


if __name__ == "__main__":
    main()
