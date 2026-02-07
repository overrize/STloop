"""pyOCD 自动化测试模块"""
from pathlib import Path
from typing import Optional, Callable

try:
    from pyocd.core.helpers import ConnectHelper
    from pyocd.flash.file_programmer import FileProgrammer
    from pyocd.core.target import Target
    from pyocd.debug.elf.symbols import ELFSymbolProvider
except ImportError:
    ConnectHelper = None


def run_with_probe(
    elf_path: Path,
    target_override: str = "stm32f411re",
    probe_id: Optional[str] = None,
    test_fn: Optional[Callable] = None,
) -> bool:
    """烧录 ELF 并运行测试。"""
    if ConnectHelper is None:
        raise RuntimeError("请安装 pyocd: pip install pyocd")

    options = {"frequency": 4_000_000, "target_override": target_override}
    if probe_id:
        options["unique_id"] = probe_id

    with ConnectHelper.session_with_chosen_probe(options=options) as session:
        FileProgrammer(session).program(str(elf_path))
        target = session.target
        target.elf = str(elf_path)
        target.reset_and_halt()
        target.resume()
        if test_fn:
            return test_fn(session, target)
        return True


def test_breakpoint_at_main(elf_path: Path, target_override: str = "stm32f411re") -> bool:
    """验证程序能在 main 处停下（断点测试）"""
    if ConnectHelper is None:
        return False

    options = {"frequency": 4_000_000, "target_override": target_override}
    with ConnectHelper.session_with_chosen_probe(options=options) as session:
        FileProgrammer(session).program(str(elf_path))
        target = session.target
        target.elf = str(elf_path)
        provider = ELFSymbolProvider(str(elf_path))
        main_addr = provider.get_symbol_value("main")
        if main_addr is None:
            return False
        target.set_breakpoint(main_addr)
        target.reset()
        while target.get_state() != Target.State.HALTED:
            pass
        pc = target.read_core_register("pc")
        target.remove_breakpoint(main_addr)
        return (pc & ~0x01) == (main_addr & ~0x01)
