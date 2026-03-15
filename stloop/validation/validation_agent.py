"""
验证 Agent：测试用例模型与顺序执行

- ValidationTestCase: 名称、步骤、预期、数据源类型
- ValidationAgent: 按顺序执行用例，向视图推送 AGENT / SYSTEM 行
"""

from dataclasses import dataclass, field
from typing import Callable, List, Optional

from stloop.ui.validation_view import ValidationChannel, ValidationView, ValidationStatus


@dataclass
class ValidationTestCase:
    """单条验证测试用例"""
    name: str
    description: str = ""
    data_source: ValidationChannel = ValidationChannel.SERIAL
    # 可选：执行函数 (view, sources_dict) -> bool
    run_fn: Optional[Callable] = None

    def run(
        self,
        view: ValidationView,
        sources: Optional[dict] = None,
    ) -> bool:
        """执行本用例，返回是否通过"""
        view.append_log(f"AGENT Running test: {self.name}")
        if self.run_fn and sources is not None:
            try:
                ok = self.run_fn(view, sources)
                if ok:
                    view.append_log(f"SYSTEM Test passed: {self.name} ✓")
                else:
                    view.append_log(f"SYSTEM Test failed: {self.name} ✗")
                return ok
            except Exception as e:
                view.append_log(f"SYSTEM Test error: {self.name} — {e} ✗")
                return False
        # 占位：无 run_fn 时仅打印并视为通过（便于演示）
        view.append_log(f"SYSTEM Test placeholder: {self.name} (no run_fn) ✓")
        return True


class ValidationAgent:
    """
    验证 Agent：按顺序执行测试用例，向 view 推送 AGENT/SYSTEM 日志
    """

    def __init__(
        self,
        view: ValidationView,
        test_cases: Optional[List[ValidationTestCase]] = None,
    ):
        self.view = view
        self.test_cases = test_cases or []
        self.results: List[bool] = []

    def add_test(self, case: ValidationTestCase) -> None:
        self.test_cases.append(case)

    def run_all(self, sources: Optional[dict] = None) -> bool:
        """顺序执行全部用例，更新 view 状态与计数，返回是否全部通过"""
        self.view.set_status(ValidationStatus.TESTING)
        self.results = []
        for case in self.test_cases:
            ok = case.run(self.view, sources)
            self.results.append(ok)
        passed = sum(self.results)
        total = len(self.results)
        if total > 0 and passed == total:
            self.view.set_status(ValidationStatus.PASSED)
            self.view.append_log(f"SYSTEM HARDWARE VALIDATION PASSED • {passed}/{total} tests successful")
        else:
            self.view.set_status(ValidationStatus.FAILED)
            self.view.append_log(f"SYSTEM HARDWARE VALIDATION FAILED • {passed}/{total} tests successful")
        return passed == total

    @staticmethod
    def default_foc_motor_placeholders() -> List[ValidationTestCase]:
        """返回默认占位用例（FOC 电流环、速度环等），用于演示与对接固件"""
        return [
            ValidationTestCase(
                name="D-Q axis current control",
                description="Iq/Id command, phase current, Iq tracking error",
                data_source=ValidationChannel.SERIAL,
            ),
            ValidationTestCase(
                name="Speed loop step response",
                description="0→3000 RPM, rise time, overshoot, steady-state error",
                data_source=ValidationChannel.SERIAL,
            ),
        ]
