"""
STLoop 交互式终端 — 自然语言端到端流程
用户输入需求 → 询问原理图/芯片手册 → 生成 → 编译 → 烧录
"""
import logging
import sys
from pathlib import Path
from typing import List, Optional

from .client import STLoopClient
from .llm_config import is_llm_configured

log = logging.getLogger("stloop")


PROMPT_SCHEMATIC = """
请提供原理图文件路径（PDF/图片，用于解析管脚连接），或输入 skip 跳过：
> """

PROMPT_DATASHEET = """
请提供芯片手册路径（PDF），多个用逗号分隔，或输入 skip 使用默认 STM32F411RE：
> """

PROMPT_FLASH = """
编译完成。是否烧录到设备？(y/n): """

PROMPT_REQUIREMENT = """
请描述你的需求（自然语言），例如：PA5 控制 LED 闪烁，500ms 周期
> """

SETUP_INSTRUCTIONS = """
┌─────────────────────────────────────────────────────────────────┐
│  STLoop 需要配置大模型 API 才能生成代码                           │
├─────────────────────────────────────────────────────────────────┤
│  方式一：创建 .env 文件（推荐）                                   │
│  复制 .env.example 为 .env，填入：                                │
│                                                                  │
│  # Kimi K2（参考 platform.moonshot.cn/docs/guide/agent-support）  │
│  OPENAI_API_KEY=sk-xxx                                           │
│  OPENAI_API_BASE=https://api.moonshot.cn/v1                      │
│  OPENAI_MODEL=kimi-k2-0905-preview   # 或 kimi-k2-turbo-preview  │
│                                                                  │
│  # OpenAI                                                         │
│  OPENAI_API_KEY=sk-xxx                                           │
├─────────────────────────────────────────────────────────────────┤
│  方式二：设置环境变量                                             │
│  PowerShell: $env:OPENAI_API_KEY="sk-xxx"                        │
│  Linux/Mac: export OPENAI_API_KEY=sk-xxx                         │
├─────────────────────────────────────────────────────────────────┤
│  获取 API Key：                                                  │
│  • Kimi:   https://platform.moonshot.cn/console/api-keys         │
│  • OpenAI: https://platform.openai.com/api-keys                  │
└─────────────────────────────────────────────────────────────────┘

配置完成后重新运行: python -m stloop
"""


def _extract_pdf_text(path: Path, max_chars: int = 15000) -> Optional[str]:
    """从 PDF 提取文本（可选依赖 pypdf）"""
    try:
        from pypdf import PdfReader
    except ImportError:
        return None
    try:
        reader = PdfReader(path)
        text = ""
        for page in reader.pages[:20]:  # 限制页数
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
) -> str:
    """构建发给 LLM 的完整 prompt"""
    parts = [requirement]
    if schematic_path and schematic_path.exists():
        schematic_text = _extract_pdf_text(schematic_path)
        if schematic_text:
            parts.append(f"\n\n【原理图内容参考】\n{schematic_text}")
        else:
            parts.append(f"\n\n用户提供了原理图: {schematic_path}，请结合用户需求推断管脚连接。")
    if datasheet_paths:
        for p in datasheet_paths:
            if p.exists():
                text = _extract_pdf_text(p)
                if text:
                    parts.append(f"\n\n【芯片手册参考: {p.name}】\n{text}")
                else:
                    parts.append(f"\n\n用户提供了芯片手册: {p}，目标芯片请据此确认。")
    return "".join(parts)


def _input_line(prompt: str) -> str:
    """读取一行输入"""
    try:
        return input(prompt).strip()
    except (EOFError, KeyboardInterrupt):
        return ""


def run_interactive(client: STLoopClient, output_dir: Optional[Path] = None) -> int:
    """运行交互式会话"""
    print("\n" + "=" * 50)
    print("  STLoop — STM32 自然语言端到端开发")
    print("=" * 50)
    print("  描述需求 → 提供原理图/手册（可选）→ 生成代码 → 编译 → 烧录")
    print("  输入 quit 或 exit 退出")
    print("=" * 50 + "\n")

    # 初始化时检查 LLM 配置
    if not is_llm_configured(client.work_dir):
        print(SETUP_INSTRUCTIONS)
        return 1

    requirement = _input_line(PROMPT_REQUIREMENT)
    if not requirement or requirement.lower() in ("quit", "exit", "q"):
        print("已退出。")
        return 0

    schematic_path: Optional[Path] = None
    datasheet_paths: List[Path] = []

    schematic_input = _input_line(PROMPT_SCHEMATIC)
    if schematic_input and schematic_input.lower() not in ("skip", "s", ""):
        p = Path(schematic_input.strip())
        if p.exists():
            schematic_path = p.resolve()
            print(f"  已使用原理图: {schematic_path}")
        else:
            print(f"  文件不存在，已跳过: {schematic_input}")

    datasheet_input = _input_line(PROMPT_DATASHEET)
    if datasheet_input and datasheet_input.lower() not in ("skip", "s", ""):
        for raw in datasheet_input.replace(";", ",").split(","):
            p = Path(raw.strip())
            if p.exists():
                datasheet_paths.append(p.resolve())
                print(f"  已使用芯片手册: {p.resolve()}")
            elif raw.strip():
                print(f"  文件不存在，已跳过: {raw.strip()}")

    # 生成工程前先确保 STM32Cube 依赖已下载
    print("\n检查编译依赖...")
    log.info("cube_path: %s", client.cube_path)
    while True:
        try:
            cube = client.ensure_cube()
            log.info("STM32Cube 就绪: %s", cube)
            break
        except RuntimeError as e:
            log.exception("依赖准备失败")
            print(f"\n依赖准备失败: {e}")
            from .scripts.download_cube import DOWNLOAD_FAIL_HINT

            print(DOWNLOAD_FAIL_HINT)
            retry = _input_line("是否重试? (y/n): ").strip().lower()
            if retry in ("y", "yes", "是"):
                continue
            return 1

    full_prompt = _build_llm_prompt(requirement, schematic_path, datasheet_paths or None)

    out = output_dir or client.work_dir / "output" / "generated"
    out.mkdir(parents=True, exist_ok=True)

    print("\n正在生成代码...")
    try:
        client.gen(full_prompt, out)
    except ValueError as e:
        if "OPENAI_API_KEY" in str(e) or "STLOOP_API_KEY" in str(e):
            print("错误: API Key 未正确加载。请确认 .env 或环境变量已配置。")
            print(SETUP_INSTRUCTIONS)
        else:
            print(f"错误: {e}")
        return 1
    except RuntimeError as e:
        if "401" in str(e) or "OPENAI_API_BASE" in str(e):
            print(f"生成失败: {e}")
            print("\n提示: 使用 Kimi 时需在 .env 中设置 OPENAI_API_BASE=https://api.moonshot.cn/v1")
        else:
            print(f"生成失败: {e}")
        return 1
    except Exception as e:
        print(f"生成失败: {e}")
        return 1

    print(f"工程已生成: {out}")
    print("正在编译...")
    log.info("编译工程: %s, cube: %s", out, client.cube_path)
    try:
        elf = client.build(out, cube_path=client.cube_path)
        print(f"编译完成: {elf}")
    except Exception as e:
        log.exception("编译失败")
        print(f"编译失败: {e}")
        if hasattr(e, "__cause__") and e.__cause__:
            print(f"详情: {e.__cause__}")
        return 1

    flash_input = _input_line(PROMPT_FLASH).strip().lower()
    if flash_input in ("y", "yes", "是"):
        try:
            client.flash(elf)
            print("烧录完成。")
        except Exception as e:
            print(f"烧录失败: {e}")
            return 1
    else:
        print("未烧录。可使用: python -m stloop build output/generated --flash")

    return 0


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="[stloop] %(levelname)s: %(message)s",
        stream=sys.stdout,
    )
    client = STLoopClient(work_dir=Path.cwd())
    sys.exit(run_interactive(client))
