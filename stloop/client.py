"""
STLoopClient — 可编程 API
支持 CLI 与 Python 脚本调用
"""
import logging
import shutil
from pathlib import Path
from typing import Optional, Callable

from . import _paths
from .builder import build as _build
from .flasher import flash as _flash
from .llm_client import generate_main_c
from .tester import run_with_probe

log = logging.getLogger("stloop")


class STLoopClient:
    """
    STLoop Client — 端到端 STM32 开发

    示例:
        client = STLoopClient(work_dir=".")
        client.ensure_cube()
        elf = client.build("demos/blink")
        client.flash(elf)
    """

    def __init__(
        self,
        work_dir: Optional[Path] = None,
        cube_path: Optional[Path] = None,
        target: str = "stm32f411re",
    ):
        self.work_dir = Path(work_dir or Path.cwd())
        self.cube_path = Path(cube_path) if cube_path else self.work_dir / "cube" / "STM32CubeF4"
        self.target = target

    def ensure_cube(self) -> Path:
        """确保 STM32CubeF4 存在，不存在则下载。失败时抛出 RuntimeError"""
        log.debug("ensure_cube: %s", self.cube_path)
        from .scripts.download_cube import download_cube

        self.cube_path = download_cube(self.cube_path, raise_on_fail=True)
        return self.cube_path

    def _copy_template(self, dest: Path, skip_main_c: bool = False):
        """复制工程模板到目标目录"""
        tpl = _paths.get_templates_dir() / "stm32_ll"
        if not tpl.exists():
            tpl = self.work_dir / "templates" / "stm32_ll"
        for p in tpl.rglob("*"):
            if p.is_dir():
                continue
            rel = p.relative_to(tpl)
            out = dest / rel
            if skip_main_c and "src" in rel.parts and rel.name == "main.c":
                continue
            out.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, out)

    def build(
        self,
        project_dir: Path,
        build_dir: Optional[Path] = None,
        cube_path: Optional[Path] = None,
    ) -> Path:
        """
        编译 STM32 工程。
        project_dir: 工程目录（含 CMakeLists.txt）
        返回 .elf 路径
        """
        proj = self.work_dir / project_dir if not Path(project_dir).is_absolute() else Path(project_dir)
        cube = cube_path or self.cube_path
        return _build(proj, build_dir=build_dir, cube_path=cube)

    def flash(
        self,
        firmware_path: Path,
        probe_id: Optional[str] = None,
    ) -> bool:
        """烧录固件到设备"""
        path = self.work_dir / firmware_path if not Path(firmware_path).is_absolute() else Path(firmware_path)
        return _flash(path, probe_id=probe_id, target_override=self.target)

    def test(
        self,
        elf_path: Path,
        test_fn: Optional[Callable] = None,
    ) -> bool:
        """烧录并运行自动化测试"""
        path = self.work_dir / elf_path if not Path(elf_path).is_absolute() else Path(elf_path)
        return run_with_probe(path, target_override=self.target, test_fn=test_fn)

    def gen(
        self,
        prompt: str,
        output_dir: Path,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
    ) -> Path:
        """
        根据自然语言生成工程。
        返回输出目录路径。
        """
        out = self.work_dir / output_dir if not Path(output_dir).is_absolute() else Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)
        main_c = generate_main_c(
            prompt,
            api_key=api_key,
            base_url=base_url,
            model=model,
            work_dir=self.work_dir,
        )
        (out / "src").mkdir(parents=True, exist_ok=True)
        (out / "inc").mkdir(parents=True, exist_ok=True)
        (out / "src" / "main.c").write_text(main_c, encoding="utf-8")
        self._copy_template(out, skip_main_c=True)
        return out

    def demo_blink(
        self,
        flash: bool = False,
        test: bool = False,
    ) -> Path:
        """
        运行 LED 闪烁 Demo。
        返回 .elf 路径。
        """
        self.ensure_cube()
        demos = _paths.get_demos_dir()
        if not demos.exists():
            demos = self.work_dir / "demos"
        project_dir = demos / "blink"
        if not (project_dir / "CMakeLists.txt").exists():
            self._copy_template(project_dir)
        elf = self.build(project_dir, cube_path=self.cube_path)
        if flash:
            self.flash(elf)
        if test:
            self.test(elf)
        return elf
