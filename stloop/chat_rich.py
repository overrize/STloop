"""
STLoop 交互式终端 - 重构版

使用 Rich UI 组件的现代交互界面。

流程：
1. 显示启动画面
2. 硬件选择（可选）
3. 输入需求
4. 生成代码（带进度）
5. 编译（带进度和自动修复）
6. 烧录确认
"""

import logging
import sys
from pathlib import Path
from typing import List, Optional

from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from rich.text import Text

from .client import STLoopClient
from .build_fix_policy import should_attempt_main_c_fix
from .errors import LLMError
from .llm_client import generate_main_c_fix
from .llm_config import is_llm_configured

# 新的 UI 组件
from .ui import (
    get_console,
    HardwareCatalog,
    select_mcu,
    create_progress,
    StepIndicator,
    create_spinner,
    SerialMonitor,
    create_monitor,
)
from .ui.components import (
    render_splash,
    render_header,
    create_success_panel,
    create_error_panel,
    create_info_panel,
    create_code_panel,
)

log = logging.getLogger("stloop")


def _setup_instructions(console: Console) -> bool:
    """
    交互式 API 配置向导 - Embedder 风格
    """
    from rich.prompt import Prompt, Confirm
    from rich.table import Table
    from rich.align import Align

    # 现代化欢迎面板
    console.print(
        Panel(
            Align.center(
                Text.assemble(
                    ("Welcome to ", "dim"),
                    ("STLoop", "bold cyan"),
                    ("\n", ""),
                    ("Configure your LLM API to start generating firmware", "dim"),
                )
            ),
            border_style="cyan",
            padding=(1, 2),
        )
    )

    # 提供商选择表格
    console.print("\n[dim]Select LLM Provider:[/dim]")

    providers_table = Table(show_header=False, box=None, padding=(0, 2))
    providers_table.add_column(style="cyan")
    providers_table.add_column(style="white")
    providers_table.add_column(style="dim")

    providers_table.add_row("1", "Kimi (Moonshot)", "Recommended for Chinese users")
    providers_table.add_row("2", "OpenAI", "GPT-4, GPT-3.5")
    providers_table.add_row("3", "Custom", "Other OpenAI-compatible API")

    console.print(providers_table)

    choice = Prompt.ask("\n[>] Select", choices=["1", "2", "3"], default="1")

    # 配置参数
    configs = {
        "1": ("Kimi", "https://api.moonshot.cn/v1", "kimi-k2-0905-preview"),
        "2": ("OpenAI", "https://api.openai.com/v1", "gpt-4o-mini"),
        "3": ("Custom", "", ""),
    }

    provider_name, default_base, default_model = configs[choice]

    console.print(f"\n[dim]Configure {provider_name}:[/dim]")

    # API Key 输入
    api_key = Prompt.ask("[>] API Key", password=True)
    if not api_key or not api_key.strip():
        console.print("[red][X] API Key is required[/red]")
        return False
    api_key = api_key.strip()

    # Base URL (Custom 时必填)
    if choice == "3":
        base_url = Prompt.ask("[>] API Base URL", default=default_base)
    else:
        base_url = default_base

    # Model
    model = Prompt.ask("[>] Model", default=default_model)

    # 配置摘要
    console.print("\n[dim]Configuration Summary:[/dim]")
    summary_table = Table(show_header=False, box=None, padding=(0, 2))
    summary_table.add_column(style="dim", justify="right")
    summary_table.add_column(style="white")
    summary_table.add_row("Provider:", provider_name)
    summary_table.add_row("API Key:", f"{api_key[:8]}...{api_key[-4:]}")
    summary_table.add_row("Base URL:", base_url)
    summary_table.add_row("Model:", model)
    console.print(summary_table)

    # 保存
    if Confirm.ask("\n[>] Save configuration?", default=True):
        try:
            env_path = Path.cwd() / ".env"
            env_content = f"""# STLoop Configuration
OPENAI_API_KEY={api_key}
OPENAI_API_BASE={base_url}
OPENAI_MODEL={model}
"""
            env_path.write_text(env_content, encoding="utf-8")

            import os

            os.environ["OPENAI_API_KEY"] = api_key
            os.environ["OPENAI_API_BASE"] = base_url
            os.environ["OPENAI_MODEL"] = model

            console.print(f"\n[green][OK] Configuration saved[/green]")
            console.print(f"[dim]   {env_path}[/dim]")
            return True

        except Exception as e:
            console.print(f"[red][X] Failed to save: {e}[/red]")
            import os

            os.environ["OPENAI_API_KEY"] = api_key
            os.environ["OPENAI_API_BASE"] = base_url
            os.environ["OPENAI_MODEL"] = model
            console.print("[yellow][!] Configuration set for current session only[/yellow]")
            return True
    else:
        # 仅设置当前会话
        import os

        os.environ["OPENAI_API_KEY"] = api_key
        os.environ["OPENAI_API_BASE"] = base_url
        os.environ["OPENAI_MODEL"] = model
        console.print("[yellow][!] Configuration set for current session only[/yellow]")
        return True


def _has_pypdf() -> bool:
    """检查是否安装了 pypdf"""
    try:
        import pypdf  # noqa: F401

        return True
    except ImportError:
        return False


def _extract_pdf_text(path: Path, max_chars: int = 15000) -> Optional[str]:
    """从 PDF 提取文本"""
    try:
        from pypdf import PdfReader
    except ImportError:
        return None
    try:
        reader = PdfReader(path)
        text = ""
        for page in reader.pages[:20]:
            text += page.extract_text() or ""
            if len(text) >= max_chars:
                break
        return text[:max_chars].strip() or None
    except Exception:
        return None


def _build_llm_prompt(
    requirement: str,
    schematic_path: Optional[Path] = None,
    datasheet_paths: Optional[List[Path]] = None,
    console: Optional[Console] = None,
) -> str:
    """构建 LLM prompt"""
    console = console or get_console()

    if (schematic_path or datasheet_paths) and not _has_pypdf():
        console.print("[yellow][!] pypdf not installed. Run: pip install stloop[pdf][/yellow]")

    parts = [requirement]

    if schematic_path and schematic_path.exists():
        schematic_text = _extract_pdf_text(schematic_path)
        if schematic_text:
            parts.append(f"\n\n[Schematic Reference]\n{schematic_text}")
        else:
            parts.append(f"\n\nUser provided schematic: {schematic_path}")

    if datasheet_paths:
        for p in datasheet_paths:
            if p.exists():
                text = _extract_pdf_text(p)
                if text:
                    parts.append(f"\n\n[Datasheet Reference: {p.name}]\n{text}")
                else:
                    parts.append(f"\n\nUser provided datasheet: {p}")

    return "".join(parts)


def _prompt_schematic(console: Console) -> Optional[Path]:
    """提示输入原理图路径"""
    path_str = Prompt.ask(
        "[cyan]Schematic path[/cyan] [dim](PDF/image, or press Enter to skip)[/dim]",
        default="",
        show_default=False,
    )

    if not path_str:
        return None

    path = Path(path_str.strip())
    if path.exists():
        console.print(f"[green][OK] Using schematic: {path}[/green]")
        return path.resolve()
    else:
        console.print(f"[yellow][!] File not found, skipped: {path_str}[/yellow]")
        return None


def _prompt_datasheets(console: Console) -> List[Path]:
    """提示输入芯片手册路径"""
    paths_str = Prompt.ask(
        "[cyan]Datasheet paths[/cyan] [dim](comma-separated, or press Enter for STM32F411RE)[/dim]",
        default="",
        show_default=False,
    )

    if not paths_str:
        return []

    paths = []
    for raw in paths_str.replace(";", ",").split(","):
        p = Path(raw.strip())
        if p.exists():
            paths.append(p.resolve())
            console.print(f"[green][OK] Using datasheet: {p.resolve()}[/green]")
        elif raw.strip():
            console.print(f"[yellow][!] File not found, skipped: {raw.strip()}[/yellow]")

    return paths


def _select_rtos_ui(console: Console) -> bool:
    """RTOS 选择 UI，询问用户是否使用 Zephyr RTOS"""
    from rich.table import Table

    console.print("\n[dim]Select your preferred RTOS/HAL framework:[/dim]\n")

    # 显示选项表格
    table = Table(show_header=True, header_style="bold cyan", box=None)
    table.add_column("Option", style="cyan", width=8)
    table.add_column("Framework", style="white", width=20)
    table.add_column("Description", style="dim")
    table.add_column("Size", style="yellow", width=15)

    table.add_row(
        "1",
        "CMSIS (LL)",
        "Lightweight, minimal HAL from ST\nStandard STM32 development",
        "~10 MB (minimal)",
    )
    table.add_row(
        "2",
        "Zephyr RTOS",
        "Modern RTOS with rich ecosystem\nMulti-threading, device tree, networking",
        "~500 MB (full)",
    )

    console.print(table)
    console.print()

    # 询问选择
    choice = Prompt.ask("[cyan]Your choice[/cyan]", choices=["1", "2"], default="1")

    use_zephyr = choice == "2"

    if use_zephyr:
        console.print("\n[blue][Zephyr][/blue] Selected Zephyr RTOS")
        console.print("[dim]Checking Zephyr environment...[/dim]")

        # 检查 Zephyr 环境
        from .builder import check_zephyr_environment

        is_ready, msg = check_zephyr_environment()

        if is_ready:
            console.print(f"[green][OK] {msg}[/green]")
            console.print("[dim]Project will be generated for Zephyr RTOS[/dim]")
        else:
            console.print(f"[yellow][!] {msg}[/yellow]")
            console.print(
                "[dim]Note: You can install Zephyr later or the project will use CMSIS fallback[/dim]"
            )

            if Confirm.ask("Install Zephyr now? (~2GB, 10-30 min)", default=False):
                console.print("[yellow]Installing Zephyr...[/yellow]")
                # 这里可以调用安装函数，但先简化处理
                console.print("[dim]Installation skipped for now. Project will use CMSIS.[/dim]")
                console.print(
                    "[yellow]You can install later: https://docs.zephyrproject.org[/yellow]"
                )
                use_zephyr = False
    else:
        console.print("\n[green][OK] Using CMSIS (LL) - Lightweight HAL[/green]")
        console.print("[dim]Standard STM32 Low-Level drivers, no RTOS overhead[/dim]")

    console.print()
    return use_zephyr


def _ensure_cube_with_ui(
    client: STLoopClient, console: Console, project_dir: Path = None, use_zephyr: bool = False
) -> bool:
    """确保 Cube 已就绪，带 UI 反馈和自动检测"""

    # 如果使用 Zephyr，检查 Zephyr 环境
    if use_zephyr:
        from .builder import check_zephyr_environment

        is_ready, msg = check_zephyr_environment()
        if is_ready:
            console.print(f"[green][OK] Zephyr environment ready[/green]")
            console.print(f"[dim]{msg}[/dim]")
            return True
        else:
            console.print(f"[yellow][!] {msg}[/yellow]")
            console.print("[dim]Will use CMSIS as fallback. You can install Zephyr later.[/dim]")
            # 继续检查 CMSIS 是否可用

    # 先检查本地 Cube 路径是否有效
    if client.cube_path.exists() and (client.cube_path / "Drivers").exists():
        console.print(f"[green][OK] STM32Cube ready: {client.cube_path}[/green]")
        return True

    # 检查项目是否有内置的 CMSIS（cmsis_minimal）
    if project_dir is None:
        project_dir = Path.cwd()
    project_cmsis = project_dir / "cmsis_minimal"
    if project_cmsis.exists() and (project_cmsis / "Device" / "STM32F4xx" / "Include").exists():
        console.print(f"[green][OK] Using embedded minimal CMSIS[/green]")
        return True

    # 尝试自动检测本地安装
    console.print("[dim]Scanning for local STM32CubeF4 installation...[/dim]")
    local_cube = client._detect_local_cube()

    if local_cube:
        console.print(f"\n[>] Found local STM32CubeF4:")
        console.print(f"   {local_cube}")

        if Confirm.ask("\n[>] Use this path?", default=True):
            client.cube_path = local_cube
            console.print(f"[green][OK] Using local STM32Cube: {local_cube}[/green]")
            return True
        else:
            # 用户拒绝，询问自定义路径
            custom = Prompt.ask(
                "[>] Enter custom path (or 'download' to auto-download)", default="download"
            )
            if custom.lower() != "download":
                custom_path = Path(custom).expanduser()
                if custom_path.exists() and (custom_path / "Drivers").exists():
                    client.cube_path = custom_path
                    console.print(f"[green][OK] Using: {custom_path}[/green]")
                    return True
                else:
                    console.print(f"[yellow][!] Invalid path, will download instead[/yellow]")
    else:
        console.print("[dim]No local installation found[/dim]")

    # 下载 Cube
    console.print("\n[>] STM32CubeF4 not found locally")
    console.print("[dim]You can:[/dim]")
    console.print("  1. Auto-download from GitHub (~500MB)")
    console.print("  2. Install STM32CubeMX and it will be auto-detected")
    console.print("  3. Download manually from st.com")
    console.print()

    if not Confirm.ask("[>] Auto-download STM32CubeF4 now?", default=True):
        console.print("[yellow][!] Cannot proceed without STM32CubeF4[/yellow]")
        console.print("[dim]Run 'python -m stloop cube-download' later to download[/dim]")
        return False

    console.print("[dim]Downloading from GitHub...[/dim]")

    with create_spinner("Downloading STM32CubeF4..."):
        try:
            cube = client.ensure_cube(interactive=False)
            console.print(f"[green][OK] STM32Cube ready: {cube}[/green]")
            return True
        except RuntimeError as e:
            log.exception("Download failed")
            console.print(f"\n[red][X] Download failed: {e}[/red]")

            from .scripts.download_cube import DOWNLOAD_FAIL_HINT

            console.print(
                Panel(
                    DOWNLOAD_FAIL_HINT,
                    title="[yellow]Download Failed[/yellow]",
                    border_style="yellow",
                )
            )

            if Confirm.ask("[>] Retry download?", default=True):
                return _ensure_cube_with_ui(client, console)
            return False


def _generate_code_with_ui(
    client: STLoopClient,
    prompt: str,
    output_dir: Path,
    datasheet_paths: Optional[List[Path]],
    console: Console,
) -> Optional[Path]:
    """生成代码，带 UI 反馈"""
    console.print("\n[bold cyan]Generating code...[/bold cyan]")

    try:
        with create_spinner("Querying AI Agent..."):
            out = client.gen(prompt, output_dir, datasheet_paths=datasheet_paths)

        console.print(
            create_success_panel(
                "Code generated successfully!",
                details={"Output": str(out)},
            )
        )

        # 显示生成的代码预览
        main_c_path = out / "src" / "main.c"
        if main_c_path.exists():
            code = main_c_path.read_text(encoding="utf-8")
            preview = "\n".join(code.split("\n")[:30])
            if len(code.split("\n")) > 30:
                preview += "\n..."
            console.print(create_code_panel(preview, title="main.c (preview)"))

        return out

    except ValueError as e:
        if "OPENAI_API_KEY" in str(e) or "STLOOP_API_KEY" in str(e):
            console.print("[red][X] API Key not configured[/red]")
            _setup_instructions(console)
        else:
            console.print(create_error_panel(str(e), title="Generation Failed"))
        return None

    except LLMError as e:
        console.print(create_error_panel(str(e), title="LLM Error"))
        return None

    except Exception as e:
        console.print(create_error_panel(str(e), title="Unexpected Error"))
        return None


def _build_with_ui(
    client: STLoopClient,
    project_dir: Path,
    prompt: str,
    console: Console,
    use_zephyr: bool = False,
) -> Optional[Path]:
    """编译工程，带进度和自动修复"""
    max_fix_rounds = 3
    elf = None

    for attempt in range(max_fix_rounds + 1):
        label = "Recompiling" if attempt > 0 else "Compiling"

        with create_progress() as progress:
            task = progress.add_task(f"{label}...", total=100)

            try:
                # 模拟进度更新
                for i in range(100):
                    progress.update(task, advance=1)
                    # 实际编译不需要进度更新，这里为了视觉效果
                    if i == 50:
                        elf = client.build(project_dir, use_zephyr=use_zephyr)
                        break

                console.print(
                    create_success_panel(
                        "Build completed!",
                        details={"ELF": str(elf)},
                    )
                )
                return elf

            except Exception as e:
                err_msg = str(getattr(e, "__cause__", e) or e)
                progress.stop()

                console.print(
                    create_error_panel(
                        err_msg[:500],
                        title=f"Build Failed (Attempt {attempt + 1}/{max_fix_rounds + 1})",
                    )
                )

                if attempt < max_fix_rounds:
                    can_fix, reason = should_attempt_main_c_fix(err_msg)

                    if not can_fix:
                        console.print(f"[yellow][!] Cannot auto-fix: {reason}[/yellow]")
                        return None

                    try:
                        main_c_path = project_dir / "src" / "main.c"
                        current_code = main_c_path.read_text(encoding="utf-8")

                        with create_spinner("Requesting AI fix..."):
                            fixed = generate_main_c_fix(
                                prompt, current_code, err_msg, work_dir=client.work_dir
                            )

                        main_c_path.write_text(fixed, encoding="utf-8")
                        console.print(f"[green][OK] Fixed main.c (Round {attempt + 1})[/green]")

                    except Exception as fix_e:
                        console.print(create_error_panel(str(fix_e), title="Fix Failed"))
                        return None
                else:
                    console.print(f"[red][X] Max retries ({max_fix_rounds}) exceeded[/red]")
                    return None

    return None


def _detect_debug_probe() -> bool:
    """检测是否连接了调试器 (ST-Link, J-Link, DAPLink 等)"""
    try:
        from pyocd.core.helpers import ConnectHelper

        probes = ConnectHelper.get_all_connected_probes()
        return len(probes) > 0
    except Exception:
        return False


def _flash_with_ui(client: STLoopClient, elf_path: Path, console: Console) -> bool:
    """烧录固件，带 UI 反馈"""
    console.print("\n[bold cyan]Flashing firmware...[/bold cyan]")

    try:
        with create_spinner("Connecting to device..."):
            client.flash(elf_path)

        console.print("[green][OK] Flash completed![/green]")
        return True

    except Exception as e:
        console.print(create_error_panel(str(e), title="Flash Failed"))
        return False


def run_interactive_rich(
    client: STLoopClient,
    output_dir: Optional[Path] = None,
    select_hardware: bool = False,
) -> int:
    """
    运行重构后的交互式会话

    Args:
        client: STLoopClient 实例
        output_dir: 输出目录
        select_hardware: 是否先选择硬件

    Returns:
        退出码
    """
    console = get_console()

    # 1. 显示启动画面
    console.clear()
    render_splash()

    # 2. 检查 LLM 配置
    if not is_llm_configured(client.work_dir):
        if not _setup_instructions(console):
            console.print(
                "[yellow][!] Configuration cancelled. Run 'python -m stloop' again to configure.[/yellow]"
            )
            return 1

    # 3. 硬件选择（可选）
    if select_hardware:
        console.print("\n[bold cyan]Step 1: Select Hardware[/bold cyan]")
        mcu = select_mcu(console)
        if mcu:
            console.print(f"[green][OK] Selected: {mcu.name}[/green]")
            client.target = mcu.name.lower()
        else:
            console.print("[yellow][!] Using default: STM32F411RE[/yellow]")

    # 4. 输入需求
    console.print("\n[bold cyan]Step 2: Describe Your Requirements[/bold cyan]")
    console.print(
        Panel(
            "Examples:\n"
            "  • PA5 LED blinking, 500ms period\n"
            "  • USART2 configured for 115200 baud\n"
            "  • TIM2 timer interrupt every 1ms",
            border_style="dim",
        )
    )

    requirement = Prompt.ask("[cyan]Your requirement[/cyan]")

    if not requirement or requirement.lower() in ("quit", "exit", "q"):
        console.print("[dim]Exited.[/dim]")
        return 0

    # 5. 输入原理图和手册
    console.print("\n[bold cyan]Step 3: Additional Resources (Optional)[/bold cyan]")
    schematic_path = _prompt_schematic(console)
    datasheet_paths = _prompt_datasheets(console)

    # 5.5 RTOS 选择
    console.print("\n[bold cyan]Step 4: RTOS Selection[/bold cyan]")
    use_zephyr = _select_rtos_ui(console)

    # 6. 确保依赖
    console.print("\n[bold cyan]Step 5: Preparing Dependencies[/bold cyan]")
    if not _ensure_cube_with_ui(client, console, use_zephyr=use_zephyr):
        return 1

    # 7. 生成代码
    console.print("\n[bold cyan]Step 6: Code Generation[/bold cyan]")

    from . import _paths

    out_dir = output_dir or _paths.get_projects_dir(client.work_dir) / "generated"

    full_prompt = _build_llm_prompt(requirement, schematic_path, datasheet_paths, console)

    project_dir = _generate_code_with_ui(client, full_prompt, out_dir, datasheet_paths, console)

    if not project_dir:
        return 1

    # 8. 编译
    console.print("\n[bold cyan]Step 7: Build[/bold cyan]")
    elf = _build_with_ui(client, project_dir, full_prompt, console)

    if not elf:
        console.print(
            create_error_panel(
                "Build failed. Please check the code manually.",
                suggestions=[
                    f"Project location: {project_dir}",
                    "Check main.c for syntax errors",
                    "Run 'stloop check' to verify toolchain",
                ],
            )
        )
        return 1

    # 9. 部署选择：自动检测硬件或提供智能选项
    console.print("\n[bold cyan]Step 8: Deploy & Test[/bold cyan]")

    # 检测硬件连接
    has_probe = _detect_debug_probe()

    if has_probe:
        console.print("[green][OK] Debug probe detected (ST-Link/J-Link)[/green]")
        console.print("[dim]Choose deployment method:[/dim]")
        console.print("  1. Flash to hardware (use ST-Link)")
        console.print("  2. Simulate with Renode (no hardware needed)")
        console.print("  3. Skip")

        deploy_choice = Prompt.ask(
            "[>] Select",
            choices=["1", "2", "3"],
            default="1",
        )
    else:
        console.print("[yellow][!] No debug probe detected[/yellow]")
        console.print("[dim]Choose deployment method:[/dim]")
        console.print("  1. Flash to hardware (requires ST-Link)")
        console.print("  2. Simulate with Renode [Recommended - no hardware needed]")
        console.print("  3. Skip")

        deploy_choice = Prompt.ask(
            "[>] Select",
            choices=["1", "2", "3"],
            default="2",
        )

    if deploy_choice == "1":
        # 烧录到真实硬件
        flash_success = _flash_with_ui(client, elf, console)
        if flash_success:
            console.print(
                create_success_panel(
                    "Flash completed! Firmware is running on the device.",
                    details={
                        "Project": str(project_dir),
                        "ELF": str(elf),
                    },
                )
            )
            # 串口监控
            if Confirm.ask(
                "\n[>] Start Serial Monitor to view device output?",
                default=False,
            ):
                _start_serial_monitor_ui(console)
        else:
            console.print(f"[yellow][!] Flash failed. You can try:[/yellow]")
            console.print(f"  [cyan]stloop build {project_dir} --flash[/cyan]")
            # 烧录失败后询问是否切换到仿真
            if Confirm.ask("\n[>] Try Renode simulation instead?", default=True):
                _run_renode_simulation_ui(elf, client.target or "stm32f411re", console)

    elif deploy_choice == "2":
        # Renode 仿真
        _run_renode_simulation_ui(elf, client.target or "stm32f411re", console)

    else:
        # 跳过
        console.print(f"[dim]Skipped. You can run later with:[/dim]")
        console.print(f"  [cyan]stloop sim {elf}[/cyan]")
        console.print(f"  [cyan]stloop build {project_dir} --flash[/cyan]")

    return 0


def _run_renode_simulation_ui(elf_path: Path, mcu: str, console: Console) -> None:
    """
    运行 Renode 仿真 UI

    Args:
        elf_path: ELF 文件路径
        mcu: MCU 型号
        console: Console 实例
    """
    from .simulators import RenodeSimulator, generate_resc_script, get_platform_file

    render_header("Renode Simulation", subtitle=mcu.upper())

    # 检查 Renode 是否安装
    sim = RenodeSimulator()
    if not sim.is_installed():
        console.print("[red][X] Renode not found[/red]")
        console.print("")
        console.print("[cyan]Installation options:[/cyan]")
        console.print("  1. Official package: https://renode.io/#downloads")
        console.print("  2. Build from source: git clone https://github.com/renode/renode.git")
        console.print("")
        console.print("[dim]After installation, make sure 'renode' command is in your PATH.[/dim]")
        return

    console.print("[green][OK] Renode found[/green]")

    # 检查 MCU 支持
    platform = get_platform_file(mcu)
    if platform:
        console.print(f"[green][OK] Platform: {platform}[/green]")
    else:
        console.print(f"[yellow][!] Unknown MCU: {mcu}, using generic STM32F4[/yellow]")

    # 生成配置和脚本
    config = type(
        "Config",
        (),
        {
            "mcu": mcu,
            "gdb_port": 3333,
            "telnet_port": 1234,
            "pause_on_startup": False,
            "show_gui": True,
            "enable_uart": True,
        },
    )()

    resc_script = generate_resc_script(elf_path, mcu=mcu, config=config)
    console.print(f"[green][OK] Generated: {resc_script.name}[/green]")

    # 启动选项
    console.print("")
    console.print("[cyan]Starting simulation...[/cyan]")
    console.print("[dim]Options:[/dim]")
    console.print("  - UART output will be shown in terminal")
    console.print("  - GDB server on port 3333")
    console.print("  - Press Ctrl+C to stop")
    console.print("")

    try:
        # 启动仿真（阻塞模式）
        result = sim.start(elf_path, mcu=mcu, config=config, blocking=True, timeout=60)

        if result:
            console.print("[green][OK] Simulation completed successfully[/green]")
        else:
            console.print("[yellow][!] Simulation ended[/yellow]")

    except KeyboardInterrupt:
        console.print("\n[yellow][!] Simulation interrupted by user[/yellow]")
        sim.stop()
    except Exception as e:
        console.print(f"[red][X] Simulation error: {e}[/red]")


def _start_serial_monitor_ui(console: Console) -> None:
    """
    启动串口监控 UI

    提供串口选择并启动实时监控。
    """
    # 列出可用串口
    ports = SerialMonitor.list_ports()

    if not ports:
        console.print("[yellow][!] No serial ports found[/yellow]")
        console.print("[dim]Connect your device and try again.[/dim]")
        return

    # 显示可用串口
    console.print("\n[bold cyan]Available Serial Ports:[/bold cyan]")
    for i, port in enumerate(ports, 1):
        console.print(f"  {i}. [green]{port['device']}[/green] - {port['description']}")

    # 选择串口
    port_idx = Prompt.ask(
        "[cyan]Select port (number)[/cyan]",
        default="1",
    )

    try:
        idx = int(port_idx) - 1
        if 0 <= idx < len(ports):
            selected_port = ports[idx]["device"]
        else:
            console.print("[red][X] Invalid selection[/red]")
            return
    except ValueError:
        console.print("[red][X] Invalid input[/red]")
        return

    # 选择波特率
    baudrate = Prompt.ask(
        "[cyan]Baudrate[/cyan]",
        default="115200",
        choices=["9600", "19200", "38400", "57600", "115200", "230400", "460800", "921600"],
    )

    # 启动监控
    monitor = SerialMonitor(console)

    if monitor.connect(selected_port, int(baudrate)):
        console.print(f"[green][OK] Connected to {selected_port} @ {baudrate} baud[/green]")
        console.print("[dim]Press Ctrl+C to stop monitoring[/dim]\n")

        try:
            monitor.start_live(refresh_rate=10)
        except KeyboardInterrupt:
            console.print("\n[yellow][!] Monitoring stopped by user[/yellow]")
        finally:
            monitor.disconnect()
            console.print("[green][OK] Disconnected[/green]")
    else:
        console.print(f"[red][X] Failed to connect to {selected_port}[/red]")


# 保持向后兼容的别名
run_interactive = run_interactive_rich
