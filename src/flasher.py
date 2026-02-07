"""pyOCD 烧录模块"""
from pathlib import Path
from typing import Optional

try:
    from pyocd.core.helpers import ConnectHelper
    from pyocd.flash.file_programmer import FileProgrammer
except ImportError:
    ConnectHelper = None
    FileProgrammer = None


def flash(
    firmware_path: Path,
    probe_id: Optional[str] = None,
    target_override: str = "stm32f411re",
    frequency: int = 4_000_000,
) -> bool:
    """
    使用 pyOCD 烧录固件到设备。
    firmware_path: .elf 或 .bin 路径
    """
    if ConnectHelper is None or FileProgrammer is None:
        raise RuntimeError("请安装 pyocd: pip install pyocd")

    options = {
        "frequency": frequency,
        "target_override": target_override,
    }
    if probe_id:
        options["unique_id"] = probe_id

    with ConnectHelper.session_with_chosen_probe(options=options) as session:
        FileProgrammer(session).program(str(firmware_path))
        session.board.target.reset()
    return True
