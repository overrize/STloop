"""Build Agent - 自动构建与错误修复

负责：
1. 执行 west build
2. 解析构建错误
3. 调用 LLM 分析并生成修复
4. 自动应用修复并重新构建
5. 支持多次重试直到成功或达到上限
"""

import logging
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

from ..llm_client import generate_code
from ..errors import BuildError

log = logging.getLogger("stloop.build_agent")


@dataclass
class BuildResult:
    """构建结果"""

    success: bool
    elf_path: Optional[Path] = None
    output: str = ""
    error: str = ""
    fix_applied: bool = False
    fix_description: str = ""


@dataclass
class BuildError:
    """构建错误信息"""

    error_type: str  # compile, link, config, etc.
    file_path: Optional[str]
    line_number: Optional[int]
    message: str
    raw_output: str


class BuildAgent:
    """构建 Agent - 自动构建与智能修复"""

    def __init__(self, max_fix_attempts: int = 3):
        self.max_fix_attempts = max_fix_attempts

    def build_with_fix(
        self,
        project_dir: Path,
        board: str,
        timeout: int = 300,
    ) -> BuildResult:
        """构建项目，失败时自动修复

        Args:
            project_dir: 项目目录
            board: 目标板
            timeout: 超时时间（秒）

        Returns:
            BuildResult: 构建结果
        """
        log.info(f"[Build] 开始构建: {project_dir}")

        for attempt in range(1, self.max_fix_attempts + 1):
            log.info(f"[Build] 尝试 {attempt}/{self.max_fix_attempts}")

            result = self._run_build(project_dir, board, timeout)

            if result.success:
                log.info(f"[Build] ✓ 构建成功")
                return result

            log.warning(f"[Build] ✗ 构建失败，分析错误...")

            # 解析错误
            errors = self._parse_errors(result.output)

            if not errors:
                log.error(f"[Build] 无法解析错误，放弃修复")
                return result

            # 生成修复
            if attempt < self.max_fix_attempts:
                fix_success = self._apply_fix(project_dir, errors, board)
                if not fix_success:
                    log.error(f"[Build] 修复应用失败")
                    return result
            else:
                log.error(f"[Build] 达到最大修复次数")
                return result

        return result

    def _run_build(
        self,
        project_dir: Path,
        board: str,
        timeout: int,
    ) -> BuildResult:
        """执行一次构建"""
        cmd = ["west", "build", "-p", "auto", "-b", board, str(project_dir)]

        log.debug(f"[Build] 命令: {' '.join(cmd)}")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
            )

            output = result.stdout + "\n" + result.stderr

            if result.returncode == 0:
                # 查找 ELF 文件
                elf_path = self._find_elf(project_dir)
                return BuildResult(
                    success=True,
                    elf_path=elf_path,
                    output=output,
                )
            else:
                return BuildResult(
                    success=False,
                    output=output,
                    error=f"构建失败 (code {result.returncode})",
                )

        except subprocess.TimeoutExpired:
            return BuildResult(
                success=False,
                error=f"构建超时 ({timeout}s)",
            )
        except Exception as e:
            return BuildResult(
                success=False,
                error=f"构建异常: {e}",
            )

    def _find_elf(self, project_dir: Path) -> Optional[Path]:
        """查找生成的 ELF 文件"""
        build_dir = project_dir / "build"
        elf = build_dir / "zephyr" / "zephyr.elf"

        if elf.exists():
            return elf

        # 搜索其他可能的位置
        for elf_file in build_dir.rglob("*.elf"):
            return elf_file

        return None

    def _parse_errors(self, output: str) -> List[BuildError]:
        """解析构建错误输出

        支持解析的错误类型：
        - GCC 编译错误
        - 链接错误
        - CMake 配置错误
        - Zephyr 设备树错误
        """
        errors = []

        # GCC 编译错误模式
        # 示例: /path/to/file.c:123:45: error: 'foo' undeclared
        gcc_pattern = r"([^:]+):(\d+):(\d+):\s*(error|warning):\s*(.+)"

        for match in re.finditer(gcc_pattern, output):
            file_path = match.group(1)
            line_num = int(match.group(2))
            severity = match.group(4)
            message = match.group(5)

            if severity == "error":
                errors.append(
                    BuildError(
                        error_type="compile",
                        file_path=file_path,
                        line_number=line_num,
                        message=message,
                        raw_output=output,
                    )
                )

        # 链接错误模式
        # 示例: undefined reference to `foo'
        link_pattern = r"(undefined reference to|cannot find|multiple definition of)\s*[\`\']?(\w+)"

        for match in re.finditer(link_pattern, output):
            errors.append(
                BuildError(
                    error_type="link",
                    file_path=None,
                    line_number=None,
                    message=match.group(0),
                    raw_output=output,
                )
            )

        # CMake 配置错误
        cmake_pattern = r"CMake Error.*:\s*(.+)"
        for match in re.finditer(cmake_pattern, output):
            errors.append(
                BuildError(
                    error_type="config",
                    file_path=None,
                    line_number=None,
                    message=match.group(1),
                    raw_output=output,
                )
            )

        # Zephyr 设备树错误
        dts_pattern = r"(devicetree error|DTS compilation failed).*:\s*(.+)"
        for match in re.finditer(dts_pattern, output, re.IGNORECASE):
            errors.append(
                BuildError(
                    error_type="devicetree",
                    file_path=None,
                    line_number=None,
                    message=match.group(2),
                    raw_output=output,
                )
            )

        log.info(f"[Build] 解析到 {len(errors)} 个错误")
        return errors

    def _apply_fix(
        self,
        project_dir: Path,
        errors: List[BuildError],
        board: str,
    ) -> bool:
        """应用修复

        通过 LLM 分析错误并生成修复代码
        """
        log.info(f"[Build] 生成修复方案...")

        # 读取当前代码
        main_c = project_dir / "src" / "main.c"
        if not main_c.exists():
            log.error(f"[Build] 找不到 main.c")
            return False

        current_code = main_c.read_text()

        # 构建修复提示
        error_context = self._build_error_context(errors)

        fix_prompt = f"""
你是一位 Zephyr RTOS 专家。请修复以下构建错误。

当前代码 (main.c):
```c
{current_code}
```

构建错误:
{error_context}

目标开发板: {board}

请分析错误原因并提供修复后的完整代码。注意:
1. 修复所有编译错误
2. 确保使用正确的 Zephyr API
3. 检查设备树节点引用
4. 包含必要的头文件
5. 保持原有功能逻辑

只输出修复后的完整 C 代码，不要输出解释。
"""

        try:
            # 调用 LLM 生成修复
            fixed_code = generate_code(
                prompt=fix_prompt,
                board=board,
                temperature=0.1,  # 低温度以获得确定性修复
            )

            # 提取代码块
            fixed_code = self._extract_code(fixed_code)

            # 备份原文件
            backup = main_c.with_suffix(".c.bak")
            main_c.rename(backup)

            # 写入修复后的代码
            main_c.write_text(fixed_code)

            log.info(f"[Build] ✓ 修复已应用")
            return True

        except Exception as e:
            log.error(f"[Build] 修复生成失败: {e}")
            # 恢复原文件
            if backup.exists():
                backup.rename(main_c)
            return False

    def _build_error_context(self, errors: List[BuildError]) -> str:
        """构建错误上下文"""
        lines = []
        for i, err in enumerate(errors[:5], 1):  # 最多显示5个错误
            lines.append(f"{i}. [{err.error_type.upper()}]")
            if err.file_path:
                lines.append(f"   文件: {err.file_path}")
            if err.line_number:
                lines.append(f"   行号: {err.line_number}")
            lines.append(f"   错误: {err.message}")
            lines.append("")

        return "\n".join(lines)

    def _extract_code(self, text: str) -> str:
        """从 LLM 输出中提取代码"""
        # 尝试提取 ```c ... ``` 块
        if "```c" in text:
            start = text.find("```c") + 4
            end = text.find("```", start)
            if end != -1:
                return text[start:end].strip()

        # 尝试提取 ``` ... ``` 块
        if "```" in text:
            start = text.find("```") + 3
            end = text.find("```", start)
            if end != -1:
                return text[start:end].strip()

        # 返回原始文本
        return text.strip()
