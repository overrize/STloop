"""Validation Agent - 功能验证与需求匹配

负责：
1. 比较实际行为与预期需求
2. 分析串口日志判断功能是否正确
3. 调用 LLM 进行智能验证
4. 生成验证报告
"""

import logging
from dataclasses import dataclass
from typing import Dict, List, Optional

from ..llm_client import generate_code

log = logging.getLogger("stloop.validation_agent")


@dataclass
class ValidationResult:
    """验证结果"""

    success: bool
    match_score: float  # 0-1
    analysis: str
    error: str = ""
    serial_logs: str = ""
    suggestions: List[str] = None

    def __post_init__(self):
        if self.suggestions is None:
            self.suggestions = []


class ValidationAgent:
    """验证 Agent - 智能功能验证"""

    def __init__(self):
        self.debug_session = None

    def validate(
        self,
        board: str,
        expected_behavior: str,
        timeout: int = 30,
        serial_logs: Optional[List[str]] = None,
    ) -> ValidationResult:
        """验证实际行为是否符合预期

        Args:
            board: 目标板
            expected_behavior: 期望的行为描述
            timeout: 验证超时
            serial_logs: 串口日志（可选，会启动新的监控会话）

        Returns:
            ValidationResult: 验证结果
        """
        log.info(f"[Validate] 开始验证")
        log.info(f"[Validate] 预期行为: {expected_behavior[:100]}...")

        # 获取串口日志
        if serial_logs is None:
            from .debug_agent import DebugAgent

            debug = DebugAgent()
            session = debug.start_monitoring()

            # 等待一段时间收集数据
            import time

            time.sleep(timeout)

            session = debug.stop_monitoring()
            serial_logs = session.serial_logs

        log_text = "\n".join(serial_logs[-100:])  # 最近100条

        # 如果日志为空，可能是程序未运行
        if not log_text.strip():
            return ValidationResult(
                success=False,
                match_score=0.0,
                analysis="未捕获到串口日志，程序可能未正常运行",
                error="No serial output captured",
                serial_logs="",
                suggestions=[
                    "检查程序是否正确烧录",
                    "检查串口连接",
                    "确认程序包含 printk 或日志输出",
                ],
            )

        # 使用 LLM 进行智能验证
        return self._llm_validate(log_text, expected_behavior, board)

    def _llm_validate(
        self,
        serial_logs: str,
        expected_behavior: str,
        board: str,
    ) -> ValidationResult:
        """使用 LLM 验证"""

        prompt = f"""
你是一位嵌入式系统验证专家。请分析以下串口日志，判断程序行为是否符合预期。

目标开发板: {board}

预期行为:
{expected_behavior}

串口日志:
```
{serial_logs[-2000:]}  # 最近2000字符
```

请分析:
1. 程序是否正常启动？
2. 观察到的实际行为是什么？
3. 是否符合预期？
4. 如果有偏差，差异在哪里？
5. 可能的修复建议？

以 JSON 格式输出:
{{
    "success": true/false,
    "match_score": 0-1,
    "analysis": "详细分析",
    "issues": ["问题1", "问题2"],
    "suggestions": ["建议1", "建议2"]
}}
"""

        try:
            response = generate_code(
                prompt=prompt,
                board=board,
                temperature=0.3,
            )

            # 尝试解析 JSON
            import json
            import re

            # 提取 JSON 块
            json_match = re.search(r"\{.*\}", response, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())

                return ValidationResult(
                    success=result.get("success", False),
                    match_score=result.get("match_score", 0.0),
                    analysis=result.get("analysis", ""),
                    serial_logs=serial_logs,
                    suggestions=result.get("suggestions", []),
                )

        except Exception as e:
            log.error(f"[Validate] LLM 验证失败: {e}")

        # 降级到简单验证
        return self._simple_validate(serial_logs, expected_behavior)

    def _simple_validate(
        self,
        serial_logs: str,
        expected_behavior: str,
    ) -> ValidationResult:
        """简单验证（LLM 失败时的降级方案）"""

        # 检查错误关键词
        error_keywords = ["error", "fail", "assert", "panic", "fault"]
        has_errors = any(kw in serial_logs.lower() for kw in error_keywords)

        if has_errors:
            return ValidationResult(
                success=False,
                match_score=0.2,
                analysis="检测到错误或异常",
                serial_logs=serial_logs,
                suggestions=["检查串口日志中的错误信息", "可能需要修复代码"],
            )

        # 检查是否有正常输出
        if len(serial_logs.strip()) > 10:
            return ValidationResult(
                success=True,
                match_score=0.6,
                analysis="程序有输出，但未进行深度验证",
                serial_logs=serial_logs,
                suggestions=["建议进行更详细的验证"],
            )

        return ValidationResult(
            success=False,
            match_score=0.0,
            analysis="无法验证，日志内容不足",
            serial_logs=serial_logs,
            suggestions=["增加程序日志输出", "检查串口连接"],
        )
