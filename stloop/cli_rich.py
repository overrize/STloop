"""STLoop CLI 入口 - 重构版"""

import argparse
import logging
import sys
from pathlib import Path

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from . import __version__
from .client import STLoopClient

# 新的 UI 组件
from .ui import get_console, HardwareCatalog, select_mcu, SerialMonitor
from .ui.components import (
    render_splash,
    render_header,
    create_success_panel,
    create_error_panel,
    create_info_panel,
    create_progress,
    StepIndicator,
)

# 保持向后兼容：优先使用新版，失败时回退到旧版
try:
    from .chat_rich import run_interactive_rich as run_interactive
except ImportError:
    from .chat import run_interactive

logging.basicConfig(
    level=logging.INFO,
    format="[stloop] %(levelname)s: %(message)s",
    stream=sys.stdout,
)


def _print_error(message: str, hint: str = "") -> None:
    """打印错误信息（兼容旧版本）"""
    console = get_console()
    console.print(create_error_panel(message, suggestions=[hint] if hint else None))


def _print_success(message: str, **kwargs) -> None:
    """打印成功信息"""
    console = get_console()
    console.print(create_success_panel(message, details=kwargs if kwargs else None))


def main() -> int:
    console = get_console()

    parser = argparse.ArgumentParser(
        prog="stloop",
        description="STLoop - AI Firmware Engineer",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("-C", "--work-dir", type=Path, default=Path.cwd(), help="Working directory")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable DEBUG logging")
    parser.add_argument("--simple", action="store_true", help="Use simple UI (fallback)")
    parser.add_argument("--select-hw", action="store_true", help="Select hardware before starting")

    sub = parser.add_subparsers(dest="cmd", required=False)

    # chat — 交互式终端（默认）
    p_chat = sub.add_parser("chat", help="Interactive session (default)")
    p_chat.add_argument("-o", "--output", type=Path, help="Project output directory")
    p_chat.add_argument("--select-hw", action="store_true", help="Select hardware first")
    p_chat.set_defaults(func=_cmd_chat)

    # demo
    p_demo = sub.add_parser("demo", help="Run Demo")
    p_demo.add_argument("scenario", choices=["blink"], help="Demo scenario")
    p_demo.add_argument("--flash", action="store_true", help="Flash to device")
    p_demo.add_argument("--test", action="store_true", help="Run automated test")
    p_demo.set_defaults(func=_cmd_demo)

    # gen
    p_gen = sub.add_parser("gen", help="Generate project from natural language")
    p_gen.add_argument("prompt", help="Requirement description, e.g.: PA5 LED blinking")
    p_gen.add_argument("-o", "--output", type=Path, help="Output directory")
    p_gen.add_argument("--build", action="store_true", help="Build after generation")
    p_gen.add_argument("--flash", action="store_true", help="Flash after build")
    p_gen.add_argument("--monitor", action="store_true", help="Start serial monitor after flash")
    p_gen.add_argument(
        "--sim", action="store_true", help="Simulate with Renode after build (instead of flash)"
    )
    p_gen.add_argument(
        "--mcu",
        type=str,
        default="STM32F411RE",
        help="MCU model for simulation (default: STM32F411RE)",
    )
    p_gen.set_defaults(func=_cmd_gen)

    # catalog - 新增：硬件目录
    p_catalog = sub.add_parser("catalog", help="Browse hardware catalog")
    p_catalog.add_argument(
        "--family", choices=["STM32", "ESP32", "NRF52", "RP2"], help="Filter by family"
    )
    p_catalog.set_defaults(func=_cmd_catalog)

    # cube-download
    p_cube = sub.add_parser("cube-download", help="Download STM32CubeF4")
    p_cube.add_argument("-o", "--output", type=Path, help="Output directory")
    p_cube.set_defaults(func=_cmd_cube_download)

    # check
    p_check = sub.add_parser("check", help="Check toolchain and dependencies")
    p_check.set_defaults(func=_cmd_check)

    # build
    p_build = sub.add_parser("build", help="Build project")
    p_build.add_argument("project", type=Path, help="Project directory")
    p_build.add_argument("--flash", action="store_true", help="Flash after build")
    p_build.add_argument("--monitor", action="store_true", help="Start serial monitor after flash")
    p_build.set_defaults(func=_cmd_build)

    # monitor - 串口监控
    p_monitor = sub.add_parser("monitor", help="Start serial monitor")
    p_monitor.add_argument("--port", type=str, help="Serial port (e.g. COM3)")
    p_monitor.add_argument("--baud", type=int, default=115200, help="Baudrate (default: 115200)")
    p_monitor.set_defaults(func=_cmd_monitor)

    # sim - Renode 仿真
    p_sim = sub.add_parser("sim", help="Start Renode simulation")
    p_sim.add_argument("elf", type=Path, nargs="?", help="ELF file to simulate")
    p_sim.add_argument(
        "--mcu", type=str, default="STM32F411RE", help="MCU model (default: STM32F411RE)"
    )
    p_sim.add_argument("--timeout", type=int, help="Simulation timeout in seconds")
    p_sim.add_argument("--gui", action="store_true", help="Show Renode GUI")
    p_sim.add_argument(
        "--generate-only", action="store_true", help="Only generate .resc script, don't run"
    )
    p_sim.set_defaults(func=_cmd_sim)

    # validate - Real-World Validation
    p_validate = sub.add_parser(
        "validate", help="Real-world hardware validation (serial, JTAG, LA, scope)"
    )
    p_validate.add_argument("--port", type=str, default="", help="Serial port (e.g. COM3)")
    p_validate.add_argument(
        "--no-run", action="store_true", help="Show validation UI only, do not run tests"
    )
    p_validate.set_defaults(func=_cmd_validate)

    args = parser.parse_args()

    if getattr(args, "verbose", False):
        logging.getLogger("stloop").setLevel(logging.DEBUG)

    # 无子命令时进入交互式 chat
    if args.cmd is None:
        args.cmd = "chat"
        args.func = _cmd_chat
        args.output = None

    client = STLoopClient(work_dir=args.work_dir)

    # 工具链检查（除 check、cube-download、validate、仅 gen 不编译外）
    if args.cmd not in ("check", "cube-download", "validate") and not (
        args.cmd == "gen" and not getattr(args, "build", False)
    ):
        try:
            from .builder import TOOLCHAIN_HINT, ensure_toolchain

            ensure_toolchain()
        except RuntimeError as e:
            _print_error(f"Toolchain check failed: {e}", TOOLCHAIN_HINT)
            return 1

    return args.func(client, args)


def _cmd_chat(client: STLoopClient, args) -> int:
    """交互式会话命令"""
    return run_interactive(
        client,
        output_dir=getattr(args, "output", None),
        select_hardware=getattr(args, "select_hw", False),
    )


def _cmd_demo(client: STLoopClient, args) -> int:
    """Demo 命令"""
    console = get_console()

    if args.scenario == "blink":
        render_header("Blink Demo", subtitle="STM32F411RE")

        try:
            with create_progress() as progress:
                task = progress.add_task("Building...", total=100)
                elf = client.demo_blink(flash=args.flash, test=args.test)
                progress.update(task, completed=100)

            _print_success("Demo completed!", ELF=str(elf))
            return 0

        except Exception as e:
            _print_error(str(e))
            return 1

    return 1


def _cmd_gen(client: STLoopClient, args) -> int:
    """生成工程命令"""
    console = get_console()

    from . import _paths
    from .chat_rich import (
        _ensure_cube_with_ui,
        _generate_code_with_ui,
        _build_with_ui,
        _flash_with_ui,
        _start_serial_monitor_ui,
        _run_renode_simulation_ui,
    )

    output = args.output or _paths.get_projects_dir(client.work_dir) / "generated"

    # 生成
    out = _generate_code_with_ui(client, args.prompt, output, None, console)
    if not out:
        return 1

    # 编译（如果指定）
    elf = None
    flash_success = False

    if args.build:
        if not _ensure_cube_with_ui(client, console, out):
            return 1

        elf = _build_with_ui(client, out, args.prompt, console)
        if not elf:
            return 1

        # 选择：仿真或烧录
        if args.sim:
            # Renode 仿真
            _run_renode_simulation_ui(elf, args.mcu, console)
        elif args.flash:
            # 烧录到真实硬件
            flash_success = _flash_with_ui(client, elf, console)
            if not flash_success:
                return 1

            # 启动串口监控（如果指定）
            if args.monitor and flash_success:
                _start_serial_monitor_ui(console)

    return 0


def _cmd_catalog(client: STLoopClient, args) -> int:
    """硬件目录命令"""
    console = get_console()

    render_header("Hardware Catalog")

    from .hardware.mcu_database import MCUFamily

    catalog = HardwareCatalog(console)

    # 系列过滤
    if args.family:
        family_map = {
            "STM32": MCUFamily.STM32,
            "ESP32": MCUFamily.ESP32,
            "NRF52": MCUFamily.NRF52,
            "RP2": MCUFamily.RP2,
        }
        family = family_map.get(args.family)
        if family:
            catalog.mcus = [mcu for mcu in catalog.mcus if mcu.family == family]
            catalog.filtered_mcus = catalog.mcus

    # 显示并选择
    console.print(catalog.render())
    console.print()

    # 显示详情
    mcu = catalog.get_selected()
    if mcu:
        console.print(catalog.render_details(mcu))

    return 0


def _cmd_check(client: STLoopClient, args) -> int:
    """环境检查命令"""
    console = get_console()

    render_header("Environment Check")

    table = Table(
        title="Toolchain Status",
        border_style="cyan",
        show_header=True,
    )
    table.add_column("Component", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Version/Path", style="dim")

    # 检查 arm-none-eabi-gcc
    from .builder import TOOLCHAIN_HINT, ensure_toolchain

    try:
        ensure_toolchain()
        table.add_row("arm-none-eabi-gcc", "[green]OK[/green]", "Detected")
    except RuntimeError:
        table.add_row("arm-none-eabi-gcc", "[red]Missing[/red]", TOOLCHAIN_HINT[:50])

    # 检查 CMake
    import shutil

    cmake = shutil.which("cmake")
    if cmake:
        table.add_row("CMake", "[green]OK[/green]", cmake)
    else:
        table.add_row("CMake", "[red]Missing[/red]", "Please install CMake")

    # 检查 STM32Cube
    try:
        cube = client.ensure_cube()
        table.add_row("STM32CubeF4", "[green]OK[/green]", str(cube))
    except RuntimeError as e:
        table.add_row("STM32CubeF4", "[red]Missing[/red]", str(e))

    # 检查 Python 依赖
    try:
        import pyocd

        table.add_row("pyOCD", "[green]OK[/green]", pyocd.__version__)
    except ImportError:
        table.add_row("pyOCD", "[red]Missing[/red]", "pip install pyocd")

    try:
        import openai

        table.add_row("OpenAI", "[green]OK[/green]", "Installed")
    except ImportError:
        table.add_row("OpenAI", "[red]Missing[/red]", "pip install openai")

    # 检查 Renode
    from .simulators import RenodeSimulator

    sim = RenodeSimulator()
    if sim.is_installed():
        from .simulators.renode import find_renode_bin

        renode_bin = find_renode_bin()
        table.add_row("Renode", "[green]OK[/green]", str(renode_bin))
    else:
        table.add_row("Renode", "[yellow]Optional[/yellow]", "Install for simulation")

    console.print(table)

    return 0


def _cmd_cube_download(client: STLoopClient, args) -> int:
    """下载 Cube 命令"""
    console = get_console()

    if args.output:
        client.cube_path = args.output

    from .chat_rich import _ensure_cube_with_ui

    if _ensure_cube_with_ui(client, console):
        _print_success("STM32CubeF4 downloaded successfully!")
        return 0
    return 1


def _cmd_validate(client: STLoopClient, args) -> int:
    """真实世界验证命令"""
    from .ui.validation_view import ValidationView, ValidationChannel, ValidationStatus
    from .validation import ValidationAgent
    from .validation.hardware_topology import ValidationTopology

    console = get_console()
    topology = ValidationTopology(mcu_name="STM32 N6", mcu_subtitle="TARGET MCU")
    view = ValidationView(console=console, topology=topology)
    view.set_status(ValidationStatus.TESTING)
    view.set_active_channel(ValidationChannel.SERIAL)
    view.append_log(
        "Embedder connects to serial, SWD/JTAG, logic analyzers, oscilloscopes.",
        ValidationChannel.SERIAL,
    )

    if not getattr(args, "no_run", False):
        agent = ValidationAgent(view, ValidationAgent.default_foc_motor_placeholders())
        agent.run_all(sources=None)
        view.append_log("AGENT Generating validation report...")
    else:
        view.append_log("Validation UI ready. Run without --no-run to execute tests.", channel=None)

    view.print_once()
    return 0


def _install_zephyr_ui(console) -> bool:
    """安装 Zephyr RTOS 的交互式向导"""
    import subprocess
    import os
    from pathlib import Path

    console.print("\n[bold blue]Zephyr RTOS 安装向导[/bold blue]\n")

    # 1. 检查 Python 版本
    console.print("[1/4] 检查 Python 环境...")
    if sys.version_info < (3, 8):
        console.print("[red][FAIL] 需要 Python 3.8+[/red]")
        return False
    console.print(f"[green][OK] Python {sys.version_info.major}.{sys.version_info.minor}[/green]\n")

    # 2. 安装 west
    console.print("[2/4] 安装 west 工具...")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "west"],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode == 0:
            console.print("[green][OK] west 安装成功[/green]\n")
        else:
            console.print(f"[yellow][!] west 可能已安装: {result.stderr[:100]}[/yellow]\n")
    except Exception as e:
        console.print(f"[yellow][!] west 安装检查: {e}[/yellow]\n")

    # 3. 获取 Zephyr 安装路径
    default_path = str(Path.home() / "zephyrproject")
    console.print("[3/4] 配置安装路径")
    console.print(f"[dim]默认路径: {default_path}[/dim]")

    from rich.prompt import Prompt

    custom_path = Prompt.ask("安装路径", default=default_path)
    install_path = Path(custom_path).resolve()

    # 4. 下载 Zephyr（使用 aria2c 或 git）
    console.print("\n[4/4] 下载 Zephyr RTOS (~500MB)...")
    console.print("[dim]这可能需要 5-30 分钟，取决于网络速度...[/dim]\n")

    zephyr_dir = install_path / "zephyr"

    try:
        install_path.mkdir(parents=True, exist_ok=True)

        # 尝试使用 git 克隆
        console.print("尝试克隆 Zephyr 仓库...")
        result = subprocess.run(
            [
                "git",
                "clone",
                "--depth",
                "1",
                "--branch",
                "v3.5.0",
                "https://github.com/zephyrproject-rtos/zephyr.git",
                str(zephyr_dir),
            ],
            capture_output=True,
            text=True,
            timeout=300,  # 5 分钟超时
        )

        if result.returncode != 0:
            console.print(f"[red][FAIL] Git 克隆失败: {result.stderr[:200]}[/red]")
            console.print("[yellow]提示: 检查网络连接或手动下载[/yellow]")
            console.print(
                f"[dim]手动安装指南: https://docs.zephyrproject.org/latest/develop/getting_started/index.html[/dim]"
            )
            return False

        # 5. 设置环境变量
        console.print("\n[bold]设置环境变量...[/bold]")
        console.print(f"[green]ZEPHYR_BASE = {zephyr_dir}[/green]")

        # 设置当前进程的环境变量
        os.environ["ZEPHYR_BASE"] = str(zephyr_dir)

        # 尝试更新 west 模块
        console.print("\n[dim]初始化 west 模块（可选）...[/dim]")
        try:
            subprocess.run(
                ["west", "update"], cwd=str(install_path), capture_output=True, timeout=300
            )
        except:
            pass  # 非关键步骤，失败也没关系

        console.print(f"\n[green bold][OK] Zephyr 安装成功！[/green bold]")
        console.print(f"[dim]位置: {zephyr_dir}[/dim]")
        console.print("\n[yellow]注意: 请重启终端或 IDE 以加载新的环境变量[/yellow]")

        return True

    except subprocess.TimeoutExpired:
        console.print("[red]✗ 下载超时，请检查网络连接[/red]")
        return False
    except Exception as e:
        console.print(f"[red]✗ 安装失败: {e}[/red]")
        return False


def _cmd_build(client: STLoopClient, args) -> int:
    """编译命令"""
    console = get_console()

    proj = args.project if Path(args.project).is_absolute() else client.work_dir / args.project
    proj = Path(proj).resolve()

    from .chat_rich import (
        _ensure_cube_with_ui,
        _build_with_ui,
        _flash_with_ui,
        _start_serial_monitor_ui,
    )
    from .builder import _is_zephyr_project, check_zephyr_environment
    from rich.prompt import Confirm

    # 检查是否为 Zephyr 项目并询问用户
    is_zephyr = _is_zephyr_project(proj)
    use_zephyr = False

    if is_zephyr:
        console.print("\n[blue][Zephyr][/blue] 检测到 Zephyr RTOS 项目")
        console.print("[dim]Zephyr 提供现代 RTOS 功能（多线程、设备树、丰富的驱动生态）[/dim]\n")

        # 检查 Zephyr 环境
        is_ready, msg = check_zephyr_environment()

        # 检查是否在交互式环境（TTY）
        is_interactive = sys.stdin.isatty() and sys.stdout.isatty()

        if is_ready:
            console.print(f"[green][OK] {msg}[/green]")
            if is_interactive:
                if Confirm.ask("是否使用 Zephyr RTOS 构建？", default=True):
                    use_zephyr = True
                else:
                    console.print("[yellow]将使用标准 CMSIS 构建（轻量级，无需 Zephyr）[/yellow]")
            else:
                # 非交互式环境，默认使用 Zephyr
                console.print("[dim]非交互式环境，自动使用 Zephyr RTOS[/dim]")
                use_zephyr = True
        else:
            console.print(f"[yellow][!] {msg}[/yellow]")
            console.print("[dim]Zephyr 尚未安装，使用标准 CMSIS 构建[/dim]")

            if is_interactive:
                if Confirm.ask(
                    "是否现在安装 Zephyr？（需要 ~2GB 空间和 10-30 分钟）", default=False
                ):
                    console.print("[yellow]开始安装 Zephyr...[/yellow]")
                    if _install_zephyr_ui(console):
                        console.print("[green][OK] Zephyr 安装成功！[/green]")
                        use_zephyr = Confirm.ask("是否使用 Zephyr RTOS 构建？", default=True)
                    else:
                        console.print("[red][FAIL] Zephyr 安装失败，将使用 CMSIS 构建[/red]")
                else:
                    console.print("[yellow]跳过安装，使用标准 CMSIS 构建[/yellow]")
            else:
                # 非交互式环境，跳过安装，使用 CMSIS
                console.print("[dim]非交互式环境，自动使用标准 CMSIS 构建[/dim]")

        console.print()

    # 检查依赖
    # Zephyr 项目（使用 CMSIS 模式）和 cmsis_minimal 项目不需要 STM32CubeF4
    has_cube = (proj / "cube" / "STM32CubeF4" / "Drivers").exists()
    has_cmsis = (proj / "cmsis_minimal").exists()

    # 如果是 Zephyr 项目但选择不使用 Zephyr，则当作普通 CMSIS 项目处理
    if is_zephyr and not use_zephyr:
        has_cmsis = True  # Zephyr 项目包含 cmsis_minimal

    if not has_cube and not has_cmsis and not (is_zephyr and use_zephyr):
        if not _ensure_cube_with_ui(client, console, proj):
            return 1

    # 编译
    elf = _build_with_ui(client, proj, "Build project", console, use_zephyr=use_zephyr)
    if not elf:
        return 1

    # 烧录
    flash_success = False
    if args.flash:
        flash_success = _flash_with_ui(client, elf, console)
        if not flash_success:
            return 1

    # 启动串口监控
    if args.monitor and flash_success:
        _start_serial_monitor_ui(console)

    return 0


def _cmd_monitor(client: STLoopClient, args) -> int:
    """串口监控命令"""
    from .chat_rich import _start_serial_monitor_ui

    console = get_console()

    # 如果指定了端口，直接使用
    if args.port:
        monitor = SerialMonitor(console)
        if monitor.connect(args.port, args.baud):
            console.print(f"[green][OK] Connected to {args.port} @ {args.baud} baud[/green]")
            console.print("[dim]Press Ctrl+C to stop monitoring[/dim]\n")

            try:
                monitor.start_live(refresh_rate=10)
            except KeyboardInterrupt:
                console.print("\n[yellow][!] Monitoring stopped by user[/yellow]")
            finally:
                monitor.disconnect()
                console.print("[green][OK] Disconnected[/green]")
            return 0
        else:
            console.print(f"[red][X] Failed to connect to {args.port}[/red]")
            return 1
    else:
        # 交互式选择
        _start_serial_monitor_ui(console)
        return 0


def _cmd_sim(client: STLoopClient, args) -> int:
    """Renode 仿真命令"""
    from .simulators import RenodeSimulator, generate_resc_script, list_supported_platforms
    from .simulators.renode import get_platform_file

    console = get_console()

    render_header("Renode Simulation", subtitle=args.mcu)

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
        return 1

    # 显示支持的 MCU
    if args.mcu == "list":
        console.print("[cyan]Supported STM32 platforms:[/cyan]")
        platforms = list_supported_platforms()
        for p in platforms:
            console.print(f"  {p['mcu']:20} ({p['type']})")
        return 0

    # 检查 MCU 支持
    platform = get_platform_file(args.mcu)
    if platform:
        console.print(f"[green][OK] Platform: {platform}[/green]")
    else:
        console.print(f"[yellow][!] Unknown MCU: {args.mcu}, using generic STM32F4[/yellow]")

    # 如果没有指定 ELF，查找最近生成的
    elf_path = args.elf
    if elf_path is None:
        from . import _paths

        projects_dir = _paths.get_projects_dir(client.work_dir)
        generated_dir = projects_dir / "generated"

        if generated_dir.exists():
            # 查找 build 目录下的 .elf 文件
            elf_files = list(generated_dir.rglob("*.elf"))
            if elf_files:
                elf_path = elf_files[0]
                console.print(f"[green][OK] Found ELF: {elf_path}[/green]")
            else:
                console.print("[red][X] No ELF file found[/red]")
                console.print("[dim]Please build a project first or specify the ELF file.[/dim]")
                return 1
        else:
            console.print("[red][X] No generated projects found[/red]")
            return 1
    else:
        elf_path = Path(elf_path)
        if not elf_path.exists():
            console.print(f"[red][X] ELF file not found: {elf_path}[/red]")
            return 1

    # 生成脚本
    config = sim.config = (
        sim.config
        or type(
            "Config",
            (),
            {
                "mcu": args.mcu,
                "gdb_port": 3333,
                "telnet_port": 1234,
                "pause_on_startup": False,
                "show_gui": args.gui,
                "enable_uart": True,
            },
        )()
    )

    resc_script = generate_resc_script(elf_path, mcu=args.mcu, config=config)
    console.print(f"[green][OK] Generated: {resc_script}[/green]")

    if args.generate_only:
        console.print(
            "[dim]Script generated. Run 'stloop sim' without --generate-only to start simulation.[/dim]"
        )
        return 0

    # 启动仿真
    console.print("")
    console.print("[cyan]Starting simulation...[/cyan]")
    console.print("[dim]Press Ctrl+C to stop[/dim]")
    console.print("")

    try:
        result = sim.start(
            elf_path, mcu=args.mcu, config=config, blocking=True, timeout=args.timeout
        )

        if result:
            console.print("[green][OK] Simulation completed[/green]")
            return 0
        else:
            console.print("[red][X] Simulation failed[/red]")
            return 1

    except KeyboardInterrupt:
        console.print("\n[yellow][!] Simulation interrupted by user[/yellow]")
        sim.stop()
        return 0
    except Exception as e:
        console.print(f"[red][X] Error: {e}[/red]")
        return 1


if __name__ == "__main__":
    sys.exit(main())
