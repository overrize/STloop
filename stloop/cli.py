"""STLoop CLI 入口"""
import argparse
import logging
import sys
from pathlib import Path

from . import __version__
from .chat import run_interactive
from .client import STLoopClient

logging.basicConfig(
    level=logging.INFO,
    format="[stloop] %(levelname)s: %(message)s",
    stream=sys.stdout,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="stloop",
        description="STLoop — STM32 自然语言端到端开发 Client",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("-C", "--work-dir", type=Path, default=Path.cwd(), help="工作目录")
    parser.add_argument("-v", "--verbose", action="store_true", help="输出 DEBUG 日志")

    sub = parser.add_subparsers(dest="cmd", required=False)

    # chat — 交互式终端（默认）
    p_chat = sub.add_parser("chat", help="交互式会话（默认）")
    p_chat.add_argument("-o", "--output", type=Path, help="工程输出目录")
    p_chat.set_defaults(func=_cmd_chat)

    # demo
    p_demo = sub.add_parser("demo", help="运行 Demo")
    p_demo.add_argument("scenario", choices=["blink"], help="Demo 场景")
    p_demo.add_argument("--flash", action="store_true", help="烧录到设备")
    p_demo.add_argument("--test", action="store_true", help="运行自动化测试")
    p_demo.set_defaults(func=_cmd_demo)

    # gen
    p_gen = sub.add_parser("gen", help="根据自然语言生成工程")
    p_gen.add_argument("prompt", help="需求描述，如：PA5 控制 LED 闪烁")
    p_gen.add_argument("-o", "--output", type=Path, default=Path("output/generated"), help="输出目录")
    p_gen.add_argument("--build", action="store_true", help="生成后编译")
    p_gen.add_argument("--flash", action="store_true", help="编译后烧录")
    p_gen.set_defaults(func=_cmd_gen)

    # cube-download
    p_cube = sub.add_parser("cube-download", help="下载 STM32Cube（F1/F4/F7）")
    p_cube.add_argument("-f", "--family", default="F4", help="芯片系列: F1/F4/F7")
    p_cube.add_argument("-o", "--output", type=Path, help="输出目录，默认 workspace/cube/STM32Cube{family}")
    p_cube.set_defaults(func=_cmd_cube_download)

    # build
    p_build = sub.add_parser("build", help="编译工程")
    p_build.add_argument("project", type=Path, help="工程目录")
    p_build.add_argument("--flash", action="store_true")
    p_build.set_defaults(func=_cmd_build)

    args = parser.parse_args()
    if getattr(args, "verbose", False):
        logging.getLogger("stloop").setLevel(logging.DEBUG)
    # 无子命令时进入交互式 chat
    if args.cmd is None:
        args.cmd = "chat"
        args.func = _cmd_chat
        args.output = None
    client = STLoopClient(work_dir=args.work_dir)
    return args.func(client, args)


def _cmd_chat(client: STLoopClient, args) -> int:
    return run_interactive(client, output_dir=getattr(args, "output", None))


def _cmd_demo(client: STLoopClient, args) -> int:
    if args.scenario == "blink":
        elf = client.demo_blink(flash=args.flash, test=args.test)
        print(f"编译完成: {elf}")
        return 0
    return 1


def _cmd_gen(client: STLoopClient, args) -> int:
    out = client.gen(args.prompt, args.output)
    print(f"工程已生成: {out}")
    if args.build:
        client.ensure_cube()
        elf = client.build(out, cube_path=client.cube_path)
        print(f"编译完成: {elf}")
        if args.flash:
            client.flash(elf)
            print("烧录完成")
    return 0


def _cmd_cube_download(client: STLoopClient, args) -> int:
    import sys

    from stloop import _paths
    from stloop.scripts.download_cube import get_fail_hint

    family = getattr(args, "family", "F4")
    client.family = family.upper()
    if args.output:
        client.cube_path = args.output
    else:
        client.cube_path = _paths.get_cube_dir(family, client.work_dir)
    try:
        client.ensure_cube(family=family)
    except RuntimeError as e:
        print(f"下载失败: {e}", file=sys.stderr)
        print(get_fail_hint(client.family), file=sys.stderr)
        return 1
    return 0


def _cmd_build(client: STLoopClient, args) -> int:
    client.ensure_cube()
    elf = client.build(args.project, cube_path=client.cube_path)
    print(f"编译完成: {elf}")
    if args.flash:
        client.flash(elf)
        print("烧录完成")
    return 0


if __name__ == "__main__":
    sys.exit(main())
