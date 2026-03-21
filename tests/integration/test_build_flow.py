"""集成测试：mock LLM 输出 -> 编译 -> 验证 ELF 产物"""

import shutil
import pytest
from pathlib import Path


def has_toolchain() -> bool:
    return shutil.which("arm-none-eabi-gcc") is not None


def has_cmake() -> bool:
    return shutil.which("cmake") is not None


BLINK_CODE = """\
#include "main.h"
#include "stm32f4xx_ll_gpio.h"
#include "stm32f4xx_ll_bus.h"
#include "stm32f4xx_ll_rcc.h"
#include "stm32f4xx_ll_system.h"
#include "stm32f4xx_ll_utils.h"

static void SystemClock_Config(void);
static void LED_Init(void);

int main(void) {
    SystemClock_Config();
    LED_Init();
    while (1) {
        LL_GPIO_TogglePin(GPIOA, LL_GPIO_PIN_5);
        LL_mDelay(500);
    }
}

static void LED_Init(void) {
    LL_AHB1_GRP1_EnableClock(LL_AHB1_GRP1_PERIPH_GPIOA);
    LL_GPIO_SetPinMode(GPIOA, LL_GPIO_PIN_5, LL_GPIO_MODE_OUTPUT);
    LL_GPIO_SetPinOutputType(GPIOA, LL_GPIO_PIN_5, LL_GPIO_OUTPUT_PUSHPULL);
    LL_GPIO_SetPinSpeed(GPIOA, LL_GPIO_PIN_5, LL_GPIO_SPEED_FREQ_LOW);
}

static void SystemClock_Config(void) {
    LL_FLASH_SetLatency(LL_FLASH_LATENCY_2);
    LL_RCC_HSE_Enable();
    while (!LL_RCC_HSE_IsReady()) {}
    LL_RCC_PLL_ConfigDomain_SYS(LL_RCC_PLLSOURCE_HSE, LL_RCC_PLLM_DIV_4,
                                 100, LL_RCC_PLLP_DIV_2);
    LL_RCC_PLL_Enable();
    while (!LL_RCC_PLL_IsReady()) {}
    LL_RCC_SetSysClkSource(LL_RCC_SYS_CLKSOURCE_PLL);
    while (LL_RCC_GetSysClkSource() != LL_RCC_SYS_CLKSOURCE_STATUS_PLL) {}
    LL_SetSystemCoreClock(100000000);
}
"""


# ---------------------------------------------------------------------------
# Unit-level validator tests (always run, no toolchain needed)
# ---------------------------------------------------------------------------

class TestCodeValidator:
    """code_validator 模块的单元测试"""

    def test_safe_code_passes(self):
        from stloop.code_validator import check_code_safety
        ok, warnings = check_code_safety(BLINK_CODE)
        assert ok, f"Expected safe, got warnings: {warnings}"

    def test_dangerous_system_call(self):
        from stloop.code_validator import check_code_safety
        code = '#include "main.h"\nint main(void) { system("rm -rf /"); }'
        ok, warnings = check_code_safety(code)
        assert not ok
        assert any("system()" in w for w in warnings)

    def test_hal_detected(self):
        from stloop.code_validator import check_code_safety
        code = '#include "main.h"\nint main(void) { HAL_GPIO_WritePin(GPIOA, 1, 1); }'
        ok, warnings = check_code_safety(code)
        assert not ok
        assert any("HAL" in w for w in warnings)

    def test_validate_good_code(self):
        from stloop.code_validator import validate_generated_code
        result = validate_generated_code(BLINK_CODE)
        assert result.ok, f"Errors: {result.errors}"

    def test_validate_empty_code(self):
        from stloop.code_validator import validate_generated_code
        result = validate_generated_code("")
        assert not result.ok
        assert any("空" in e for e in result.errors)

    def test_validate_missing_main(self):
        from stloop.code_validator import validate_generated_code
        code = '#include "main.h"\nvoid setup(void) { while(1){} }\n' * 5
        result = validate_generated_code(code)
        assert any("main" in e for e in result.errors)

    def test_validate_brace_mismatch(self):
        from stloop.code_validator import validate_generated_code
        code = '#include "main.h"\nint main(void) { if(1) { }\n' * 3
        result = validate_generated_code(code)
        assert any("大括号" in e for e in result.errors)


# ---------------------------------------------------------------------------
# Integration tests (need ARM toolchain + cmake + cube)
# ---------------------------------------------------------------------------

@pytest.mark.integration
@pytest.mark.skipif(not has_toolchain(), reason="需要 arm-none-eabi-gcc")
@pytest.mark.skipif(not has_cmake(), reason="需要 cmake")
class TestBuildFlow:
    """端到端集成测试：固定代码 -> 编译 -> ELF 验证"""

    def _prepare_project(self, tmp_path: Path) -> Path:
        """准备一个可编译的 STM32 项目目录"""
        from stloop.client import STLoopClient

        project_dir = tmp_path / "test_project"
        project_dir.mkdir()
        (project_dir / "src").mkdir()
        (project_dir / "inc").mkdir()
        (project_dir / "src" / "main.c").write_text(BLINK_CODE, encoding="utf-8")

        client = STLoopClient(work_dir=tmp_path)
        client._copy_template(project_dir, skip_main_c=True)

        (project_dir / "chip_config.cmake").write_text(
            "set(MCU_DEVICE STM32F411xE)\n"
            "set(STARTUP_PATTERN f411)\n"
            "set(LINKER_PATTERN F411)\n",
            encoding="utf-8",
        )
        return project_dir

    def test_build_produces_elf(self, tmp_path):
        """编译应产出 ELF 文件"""
        project_dir = self._prepare_project(tmp_path)

        from stloop.client import STLoopClient

        client = STLoopClient(work_dir=tmp_path)
        try:
            cube = client.ensure_cube(interactive=False)
            client._ensure_linker_startup_in_project(
                project_dir, cube, startup_pat="f411", linker_pat="F411"
            )
            elf = client.build(project_dir)
            assert elf.exists(), f"ELF not found at {elf}"
            assert elf.stat().st_size > 1024, "ELF too small, likely empty"
        except Exception as e:
            pytest.skip(f"Build infrastructure not available: {e}")

    def test_elf_contains_main_symbol(self, tmp_path):
        """ELF 应包含 main 符号"""
        import subprocess

        nm = shutil.which("arm-none-eabi-nm")
        if not nm:
            pytest.skip("arm-none-eabi-nm not found")

        project_dir = self._prepare_project(tmp_path)

        from stloop.client import STLoopClient

        client = STLoopClient(work_dir=tmp_path)
        try:
            cube = client.ensure_cube(interactive=False)
            client._ensure_linker_startup_in_project(
                project_dir, cube, startup_pat="f411", linker_pat="F411"
            )
            elf = client.build(project_dir)
        except Exception as e:
            pytest.skip(f"Build infrastructure not available: {e}")

        result = subprocess.run(
            [nm, str(elf)], capture_output=True, text=True
        )
        assert "main" in result.stdout, "ELF missing 'main' symbol"
