"""端到端自动化 Agent - 闭环代码生成、构建、烧录、验证

实现完全自动化的嵌入式开发流程：
1. 用户输入需求
2. AI 生成代码
3. 自动构建（失败则自修复）
4. 自动烧录（支持重试和切换工具）
5. 自动调试验证（串口、JTAG、逻辑分析仪）
6. 不满足需求则自动诊断并重新迭代
"""

import logging
import time
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Callable, List, Optional, Dict, Any
import json

from ..llm_client import generate_code
from ..errors import STLoopError

log = logging.getLogger("stloop.e2e")


class Stage(Enum):
    """流水线阶段"""

    GENERATE = auto()
    BUILD = auto()
    FLASH = auto()
    VERIFY = auto()
    COMPLETE = auto()
    FAILED = auto()


class ErrorType(Enum):
    """错误类型"""

    COMPILE_ERROR = auto()
    LINK_ERROR = auto()
    FLASH_ERROR = auto()
    RUNTIME_ERROR = auto()
    VALIDATION_ERROR = auto()
    TIMEOUT = auto()


@dataclass
class IterationResult:
    """单次迭代结果"""

    iteration: int
    stage: Stage
    success: bool
    error_type: Optional[ErrorType] = None
    error_message: str = ""
    logs: Dict[str, str] = field(default_factory=dict)
    project_path: Optional[Path] = None
    elf_path: Optional[Path] = None


@dataclass
class EndToEndResult:
    """端到端执行结果"""

    success: bool
    final_stage: Stage
    iterations: List[IterationResult]
    total_time: float
    project_path: Optional[Path] = None
    elf_path: Optional[Path] = None
    summary: str = ""


class EndToEndAgent:
    """端到端自动化 Agent

    协调 BuildAgent、FlashAgent、DebugAgent、ValidationAgent
    实现完全自动化的闭环开发流程。
    """

    def __init__(
        self,
        max_iterations: int = 5,
        build_timeout: int = 300,
        flash_timeout: int = 60,
        verify_timeout: int = 30,
        progress_callback: Optional[Callable[[str, float], None]] = None,
    ):
        self.max_iterations = max_iterations
        self.build_timeout = build_timeout
        self.flash_timeout = flash_timeout
        self.verify_timeout = verify_timeout
        self.progress_callback = progress_callback

        # 延迟导入以避免循环依赖
        from .build_agent import BuildAgent
        from .flash_agent import FlashAgent
        from .debug_agent import DebugAgent
        from .validation_agent import ValidationAgent

        self.build_agent = BuildAgent()
        self.flash_agent = FlashAgent()
        self.debug_agent = DebugAgent()
        self.validation_agent = ValidationAgent()

        self.iterations: List[IterationResult] = []

    def _report_progress(self, message: str, percent: float):
        """报告进度"""
        log.info(f"[E2E] {message} ({percent:.0f}%)")
        if self.progress_callback:
            self.progress_callback(message, percent)

    def run(
        self,
        prompt: str,
        board: str,
        output_dir: Path,
        auto_flash: bool = True,
        auto_verify: bool = True,
        expected_behavior: Optional[str] = None,
    ) -> EndToEndResult:
        """执行端到端自动化流程

        Args:
            prompt: 用户需求描述
            board: 目标开发板
            output_dir: 项目输出目录
            auto_flash: 是否自动烧录
            auto_verify: 是否自动验证
            expected_behavior: 期望的行为描述（用于验证）

        Returns:
            EndToEndResult: 执行结果
        """
        start_time = time.time()
        self.iterations = []

        log.info(f"=" * 60)
        log.info(f"[E2E] 开始端到端自动化流程")
        log.info(f"[E2E] 需求: {prompt}")
        log.info(f"[E2E] 目标板: {board}")
        log.info(f"[E2E] 最大迭代次数: {self.max_iterations}")
        log.info(f"=" * 60)

        current_project = None
        final_result = None

        for iteration in range(1, self.max_iterations + 1):
            log.info(f"\n{'=' * 60}")
            log.info(f"[E2E] 迭代 {iteration}/{self.max_iterations}")
            log.info(f"{'=' * 60}")

            iter_result = self._run_iteration(
                iteration=iteration,
                prompt=prompt,
                board=board,
                output_dir=output_dir,
                current_project=current_project,
                auto_flash=auto_flash,
                auto_verify=auto_verify,
                expected_behavior=expected_behavior,
            )

            self.iterations.append(iter_result)
            current_project = iter_result.project_path

            if iter_result.success:
                final_result = iter_result
                log.info(f"\n{'=' * 60}")
                log.info(f"[E2E] ✓ 成功完成！")
                log.info(f"[E2E] 最终阶段: {iter_result.stage.name}")
                log.info(f"[E2E] 项目路径: {iter_result.project_path}")
                log.info(f"[E2E] ELF 文件: {iter_result.elf_path}")
                log.info(f"{'=' * 60}")
                break
            else:
                log.warning(f"[E2E] 迭代 {iteration} 失败: {iter_result.error_type}")
                if iteration == self.max_iterations:
                    log.error(f"[E2E] 达到最大迭代次数，流程失败")

        total_time = time.time() - start_time

        return EndToEndResult(
            success=final_result is not None and final_result.success,
            final_stage=final_result.stage if final_result else Stage.FAILED,
            iterations=self.iterations,
            total_time=total_time,
            project_path=final_result.project_path if final_result else None,
            elf_path=final_result.elf_path if final_result else None,
            summary=self._generate_summary(),
        )

    def _run_iteration(
        self,
        iteration: int,
        prompt: str,
        board: str,
        output_dir: Path,
        current_project: Optional[Path],
        auto_flash: bool,
        auto_verify: bool,
        expected_behavior: Optional[str],
    ) -> IterationResult:
        """执行单次迭代"""

        # Stage 1: 生成代码
        self._report_progress(f"迭代 {iteration}: 生成代码", 10)

        if iteration == 1:
            # 第一次迭代：全新生成
            project_dir = self._generate_new_project(prompt, board, output_dir)
        else:
            # 后续迭代：基于错误修复
            last_error = self.iterations[-1]
            project_dir = self._fix_and_regenerate(prompt, board, current_project, last_error)

        if not project_dir:
            return IterationResult(
                iteration=iteration,
                stage=Stage.GENERATE,
                success=False,
                error_type=ErrorType.COMPILE_ERROR,
                error_message="代码生成失败",
            )

        # Stage 2: 构建
        self._report_progress(f"迭代 {iteration}: 构建项目", 30)

        build_result = self.build_agent.build_with_fix(
            project_dir=project_dir,
            board=board,
            timeout=self.build_timeout,
        )

        if not build_result.success:
            return IterationResult(
                iteration=iteration,
                stage=Stage.BUILD,
                success=False,
                error_type=ErrorType.COMPILE_ERROR
                if "error" in build_result.error.lower()
                else ErrorType.LINK_ERROR,
                error_message=build_result.error,
                logs={"build": build_result.output},
                project_path=project_dir,
            )

        elf_path = build_result.elf_path
        log.info(f"[E2E] ✓ 构建成功: {elf_path}")

        # Stage 3: 烧录（可选）
        if auto_flash:
            self._report_progress(f"迭代 {iteration}: 烧录设备", 50)

            flash_result = self.flash_agent.flash_with_retry(
                elf_path=elf_path,
                board=board,
                timeout=self.flash_timeout,
            )

            if not flash_result.success:
                return IterationResult(
                    iteration=iteration,
                    stage=Stage.FLASH,
                    success=False,
                    error_type=ErrorType.FLASH_ERROR,
                    error_message=flash_result.error,
                    logs={
                        "build": build_result.output,
                        "flash": flash_result.output,
                    },
                    project_path=project_dir,
                    elf_path=elf_path,
                )

            log.info(f"[E2E] ✓ 烧录成功")

        # Stage 4: 验证（可选）
        if auto_verify and expected_behavior:
            self._report_progress(f"迭代 {iteration}: 验证功能", 70)

            verify_result = self.validation_agent.validate(
                board=board,
                expected_behavior=expected_behavior,
                timeout=self.verify_timeout,
            )

            if not verify_result.success:
                return IterationResult(
                    iteration=iteration,
                    stage=Stage.VERIFY,
                    success=False,
                    error_type=ErrorType.VALIDATION_ERROR,
                    error_message=verify_result.error,
                    logs={
                        "build": build_result.output,
                        "flash": flash_result.output if auto_flash else "",
                        "serial": verify_result.serial_logs,
                        "analysis": verify_result.analysis,
                    },
                    project_path=project_dir,
                    elf_path=elf_path,
                )

            log.info(f"[E2E] ✓ 验证通过")

        # 成功完成
        self._report_progress(f"迭代 {iteration}: 完成", 100)

        return IterationResult(
            iteration=iteration,
            stage=Stage.COMPLETE,
            success=True,
            project_path=project_dir,
            elf_path=elf_path,
            logs={"build": build_result.output},
        )

    def _generate_new_project(
        self,
        prompt: str,
        board: str,
        output_dir: Path,
    ) -> Optional[Path]:
        """生成新项目"""
        from ..project_generator import ProjectGenerator

        try:
            generator = ProjectGenerator()
            project_dir = generator.generate(
                prompt=prompt,
                output_dir=output_dir,
                board=board,
            )
            log.info(f"[E2E] 项目生成: {project_dir}")
            return project_dir
        except Exception as e:
            log.error(f"[E2E] 项目生成失败: {e}")
            return None

    def _fix_and_regenerate(
        self,
        prompt: str,
        board: str,
        current_project: Optional[Path],
        last_error: IterationResult,
    ) -> Optional[Path]:
        """基于错误修复并重新生成"""

        log.info(f"[E2E] 基于错误修复重新生成...")
        log.info(f"[E2E] 错误类型: {last_error.error_type}")
        log.info(f"[E2E] 错误信息: {last_error.error_message[:200]}...")

        # 构建修复提示
        fix_prompt = self._build_fix_prompt(prompt, last_error)

        # 重新生成
        return self._generate_new_project(
            fix_prompt,
            board,
            current_project.parent if current_project else Path("./stloop_projects"),
        )

    def _build_fix_prompt(self, original_prompt: str, error: IterationResult) -> str:
        """构建修复提示"""

        fix_context = f"""
原始需求: {original_prompt}

上一轮失败信息:
- 阶段: {error.stage.name}
- 错误类型: {error.error_type.name if error.error_type else "Unknown"}
- 错误详情: {error.error_message}

构建日志片段:
{error.logs.get("build", "")[-1000:]}

请修复以上错误，注意:
1. 仔细检查 Zephyr API 的使用方式
2. 确保设备树节点引用正确
3. 检查头文件包含和函数签名
4. 参考 Zephyr 官方文档和示例代码

重新生成修复后的完整代码。
"""
        return fix_context

    def _generate_summary(self) -> str:
        """生成执行摘要"""
        lines = []
        lines.append("=" * 60)
        lines.append("端到端执行摘要")
        lines.append("=" * 60)

        for iter_result in self.iterations:
            status = "✓" if iter_result.success else "✗"
            lines.append(f"\n迭代 {iter_result.iteration}: {status}")
            lines.append(f"  阶段: {iter_result.stage.name}")
            if iter_result.error_type:
                lines.append(f"  错误: {iter_result.error_type.name}")
                lines.append(f"  详情: {iter_result.error_message[:100]}...")

        lines.append("\n" + "=" * 60)

        return "\n".join(lines)


# 便捷的顶层函数
def run_end_to_end(
    prompt: str,
    board: str = "nucleo_f411re",
    output_dir: Optional[Path] = None,
    auto_flash: bool = True,
    auto_verify: bool = True,
    expected_behavior: Optional[str] = None,
    max_iterations: int = 5,
    progress_callback: Optional[Callable[[str, float], None]] = None,
) -> EndToEndResult:
    """便捷的端到端执行函数

    示例:
        result = run_end_to_end(
            prompt="PA5 LED 每秒闪烁一次",
            board="nucleo_f411re",
            auto_flash=True,
            auto_verify=True,
            expected_behavior="LED 应该以 1Hz 频率闪烁",
        )

        if result.success:
            print(f"成功！ELF: {result.elf_path}")
        else:
            print(f"失败: {result.summary}")
    """
    agent = EndToEndAgent(
        max_iterations=max_iterations,
        progress_callback=progress_callback,
    )

    return agent.run(
        prompt=prompt,
        board=board,
        output_dir=output_dir or Path("./stloop_projects"),
        auto_flash=auto_flash,
        auto_verify=auto_verify,
        expected_behavior=expected_behavior,
    )
