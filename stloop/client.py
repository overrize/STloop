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
from .linker_gen import generate_linker_script
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
        """复制工程模板到目标目录。与 CubeMX 一致：不覆盖已存在的用户文件，仅补齐缺失项。"""
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
            if out.exists():
                log.debug("保留已有文件: %s", out)
                continue
            out.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, out)
            log.info("补齐模板: %s", rel)

    def _embed_cube(self, project_dir: Path, cube_path: Path) -> Path:
        """将 cube 库复制到项目内，使项目自包含。与 CubeMX 一致：lib 每次更新，确保使用最新驱动。"""
        dest = project_dir / "cube" / "STM32CubeF4"
        cube_path = Path(cube_path).resolve()
        log.info("_embed_cube: 源=%s, 目标=%s", cube_path, dest)

        dest.parent.mkdir(parents=True, exist_ok=True)
        print("  [生成] 更新 cube 库到项目（lib 保持最新）...")
        shutil.copytree(cube_path, dest, dirs_exist_ok=True, symlinks=False)
        return dest

    def _ensure_linker_startup_in_project(
        self,
        project_dir: Path,
        cube_root: Path,
        startup_pat: str,
        linker_pat: str,
    ) -> None:
        """把 .ld 和 startup_*.s 从 cube 复制到工程目录（与 src 同级），便于 CMake 优先使用。"""
        project_dir = Path(project_dir)
        cube_root = Path(cube_root)
        log.info("_ensure_linker_startup_in_project: 工程=%s, cube=%s, startup_pat=%s, linker_pat=%s",
                 project_dir, cube_root, startup_pat, linker_pat)

        # 在 cube 中找匹配的 .ld（先 Projects，再 Drivers）
        ld_candidates = list((cube_root / "Projects").rglob("*.ld")) if (cube_root / "Projects").exists() else []
        if not ld_candidates:
            ld_candidates = list((cube_root / "Drivers").rglob("*.ld"))
        ld_file = None
        for p in ld_candidates:
            if linker_pat.upper() in p.name and "FLASH" in p.name:
                ld_file = p
                break
        if not ld_file and ld_candidates:
            ld_file = ld_candidates[0]
        if ld_file:
            dest_ld = project_dir / ld_file.name
            if dest_ld != ld_file and (not dest_ld.exists() or dest_ld.stat().st_mtime < ld_file.stat().st_mtime):
                shutil.copy2(ld_file, dest_ld)
                log.info("复制 linker: %s -> %s", ld_file, dest_ld)
                print(f"  [生成] 复制链接脚本: {ld_file.name} -> 工程目录")
        else:
            log.warning("cube 中未找到匹配 *%s*FLASH*.ld，尝试生成", linker_pat)
            gen_ld = generate_linker_script(project_dir, linker_pat)
            if gen_ld:
                print(f"  [生成] 生成链接脚本: {gen_ld.name} -> 工程目录")
            else:
                log.warning("linker 生成失败，芯片 %s 可能不在支持列表", linker_pat)

        # 在 cube 中找匹配的 startup_*.s（必须用 GCC 语法，arm/ 为 Keil 语法不兼容）
        cmsis_device = cube_root / "Drivers" / "CMSIS" / "Device" / "ST" / "STM32F4xx"
        all_startup = list(cmsis_device.rglob("startup_stm32*.s")) if cmsis_device.exists() else []
        if not all_startup:
            all_startup = list((cube_root / "Drivers").rglob("startup_stm32*.s"))
        # 优先 gcc/ 目录（GNU 汇编器），排除 arm/（ARM/Keil 语法）
        gcc_startups = [p for p in all_startup if "gcc" in p.parts]
        startup_list = gcc_startups if gcc_startups else [p for p in all_startup if "arm" not in p.parts] or all_startup
        startup_file = None
        for p in startup_list:
            if startup_pat.lower() in p.name.lower():
                startup_file = p
                break
        if not startup_file and startup_list:
            startup_file = startup_list[0]
        if startup_file:
            dest_startup = project_dir / startup_file.name
            if dest_startup != startup_file and (not dest_startup.exists() or dest_startup.stat().st_mtime < startup_file.stat().st_mtime):
                shutil.copy2(startup_file, dest_startup)
                log.info("复制 startup: %s -> %s", startup_file, dest_startup)
                print(f"  [生成] 复制启动文件: {startup_file.name} -> 工程目录")
        else:
            log.warning("cube 中未找到匹配 startup_*%s*.s", startup_pat)

    def build(
        self,
        project_dir: Path,
        build_dir: Optional[Path] = None,
        cube_path: Optional[Path] = None,
    ) -> Path:
        """
        编译 STM32 工程。
        project_dir: 工程目录（含 CMakeLists.txt）
        cube_path: 显式指定时使用；否则项目有内嵌 cube 则用项目的，否则用 ensure_cube 的
        返回 .elf 路径
        """
        proj = Path(project_dir) if Path(project_dir).is_absolute() else self.work_dir / project_dir
        proj = proj.resolve()
        if cube_path is not None:
            cube = cube_path
            log.info("build: 使用显式 cube_path=%s", cube)
        elif (proj / "cube" / "STM32CubeF4" / "Drivers").exists():
            cube = None
            log.info("build: 使用项目内嵌 cube (project=%s)", proj)
        else:
            cube = self.cube_path
            log.info("build: 使用工作区 cube_path=%s", cube)
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
        embed_cube: bool = True,
        datasheet_paths: Optional[list[Path | str]] = None,
    ) -> Path:
        """
        根据自然语言生成工程。embed_cube=True 时将 cube 复制到项目内，使项目自包含。
        datasheet_paths 用于从手册文件名推断目标芯片，动态配置 startup/linker。
        返回输出目录路径。
        """
        from .chip_config import infer_chip

        out = self.work_dir / output_dir if not Path(output_dir).is_absolute() else Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)
        mcu_device, startup_pat, linker_pat = infer_chip(prompt=prompt, datasheet_paths=datasheet_paths)
        log.info("推断芯片: MCU_DEVICE=%s", mcu_device)
        print(f"  [生成] 推断芯片: {mcu_device}")
        (out / "chip_config.cmake").write_text(
            f"set(MCU_DEVICE {mcu_device})\n"
            f"set(STARTUP_PATTERN {startup_pat})\n"
            f"set(LINKER_PATTERN {linker_pat})\n",
            encoding="utf-8",
        )
        main_c = generate_main_c(
            prompt,
            api_key=api_key,
            base_url=base_url,
            model=model,
            work_dir=self.work_dir,
        )
        print("  [生成] 写入 main.c...")
        (out / "src").mkdir(parents=True, exist_ok=True)
        (out / "inc").mkdir(parents=True, exist_ok=True)
        (out / "src" / "main.c").write_text(main_c, encoding="utf-8")
        print("  [生成] 复制工程模板...")
        cube_dest = None
        if embed_cube and self.cube_path and (self.cube_path / "Drivers").exists():
            cube_dest = self._embed_cube(out, self.cube_path)
        self._copy_template(out, skip_main_c=True)
        if cube_dest is not None:
            log.info("cube 内嵌结果: %s", cube_dest)
        # linker/startup 与 lib 判断分离：放到工程目录（与 src 同级），便于编译
        if cube_dest is not None:
            self._ensure_linker_startup_in_project(out, cube_dest, startup_pat, linker_pat)
        else:
            log.warning("未内嵌 cube，跳过复制 .ld/startup 到工程目录")
        log.info("工程已生成: %s", out)
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
